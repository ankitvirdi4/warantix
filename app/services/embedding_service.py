from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Claim
from . import vector_store

LOGGER = logging.getLogger(__name__)


def _build_embedding_input(claim: Claim) -> str:
    return (
        f"Model: {claim.model}, Component: {claim.component}, Region: {claim.region}, "
        f"DTC: {claim.dtc_codes}, Symptoms: {claim.symptom_text}"
    )


def _batched(iterable: Iterable[Claim], size: int) -> Iterable[list[Claim]]:
    batch: list[Claim] = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def _get_openai_client(settings: Settings) -> OpenAI | None:
    if not settings.openai_api_key:
        LOGGER.warning("OPENAI_API_KEY not configured; skipping embedding generation")
        return None
    return OpenAI(api_key=settings.openai_api_key)


def embed_new_claims(db: Session, settings: Settings) -> int:
    client = _get_openai_client(settings)
    if client is None:
        return 0

    stmt = (
        select(Claim)
        .where(Claim.embedded_at.is_(None))
        .order_by(Claim.id.asc())
    )
    claims = db.execute(stmt).scalars().all()
    if not claims:
        return 0

    vector_store.init_vector_store(settings)

    total_embedded = 0
    batch_size = max(1, settings.embedding_batch_size)

    for batch in _batched(claims, batch_size):
        inputs = [_build_embedding_input(claim) for claim in batch]
        try:
            response = client.embeddings.create(
                model=settings.openai_embedding_model,
                input=inputs,
            )
        except Exception as exc:  # pragma: no cover - network errors
            LOGGER.exception("Failed to create embeddings: %s", exc)
            db.rollback()
            break

        embeddings = response.data
        if len(embeddings) != len(batch):
            LOGGER.error("Embedding response count %s does not match batch size %s", len(embeddings), len(batch))
            db.rollback()
            break

        points: list[vector_store.ClaimEmbedding] = []
        now = datetime.utcnow()
        for claim, data in zip(batch, embeddings):
            vector = list(data.embedding)  # type: ignore[attr-defined]
            claim.embedded_at = now
            payload = {
                "claim_id": claim.claim_id,
                "model": claim.model,
                "model_year": claim.model_year,
                "region": claim.region,
                "component": claim.component,
                "part_number": claim.part_number,
                "dtc_codes": claim.dtc_codes,
                "symptom_text": claim.symptom_text,
                "claim_cost_usd": float(claim.claim_cost_usd),
                "failure_date": claim.failure_date.isoformat() if claim.failure_date else None,
                "cluster_id": claim.cluster_id,
            }
            points.append(
                vector_store.ClaimEmbedding(
                    id=claim.id,
                    vector=vector,
                    payload=payload,
                )
            )

        try:
            vector_store.upsert_claim_embeddings(settings, points)
        except Exception as exc:  # pragma: no cover - vector DB failures
            LOGGER.exception("Failed to upsert embeddings to vector store: %s", exc)
            db.rollback()
            break

        db.commit()
        total_embedded += len(batch)

    return total_embedded
