from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List

import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Claim, Cluster
from . import vector_store

LOGGER = logging.getLogger(__name__)


def _compute_label(components: Counter, dtcs: Counter, index: int) -> str:
    label_parts: list[str] = []
    if components:
        label_parts.append(components.most_common(1)[0][0])
    if dtcs:
        label_parts.append(dtcs.most_common(1)[0][0])
    if not label_parts:
        return f"Cluster {index + 1}"
    return " / ".join(label_parts)


def _aggregate_cluster_stats(claims: Iterable[Claim], index: int) -> dict:
    num_claims = 0
    total_cost = Decimal("0")
    first_date: date | None = None
    last_date: date | None = None
    dtc_counter: Counter[str] = Counter()
    component_counter: Counter[str] = Counter()

    for claim in claims:
        num_claims += 1
        total_cost += Decimal(str(claim.claim_cost_usd))
        if claim.failure_date:
            if first_date is None or claim.failure_date < first_date:
                first_date = claim.failure_date
            if last_date is None or claim.failure_date > last_date:
                last_date = claim.failure_date
        if claim.dtc_codes:
            codes = [code.strip() for code in claim.dtc_codes.split(",") if code.strip()]
            dtc_counter.update(codes)
        if claim.component:
            component_counter.update([claim.component])

    sample_dtc = ", ".join(code for code, _ in dtc_counter.most_common(5)) or None
    sample_components = ", ".join(component for component, _ in component_counter.most_common(5)) or None
    if num_claims:
        total_cost = total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "num_claims": num_claims,
        "total_cost_usd": total_cost,
        "first_failure_date": first_date,
        "last_failure_date": last_date,
        "sample_dtc_codes": sample_dtc,
        "sample_components": sample_components,
        "label": _compute_label(component_counter, dtc_counter, index),
    }


def recalculate_clusters(db: Session, settings: Settings) -> int:
    embeddings = vector_store.fetch_all_embeddings(settings)
    if not embeddings:
        LOGGER.info("No embeddings available for clustering")
        return 0

    if len(embeddings) < settings.clustering_min_claims:
        LOGGER.info(
            "Insufficient claims for clustering: %s < %s",
            len(embeddings),
            settings.clustering_min_claims,
        )
        return 0

    vectors = np.array([embedding.vector for embedding in embeddings], dtype=np.float32)
    inferred_clusters = max(2, len(embeddings) // 50)
    k = min(settings.num_clusters_default, inferred_clusters)
    if k < 2:
        k = 2

    LOGGER.info("Running KMeans clustering with k=%s on %s claims", k, len(embeddings))
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    assignments: Dict[int, List[int]] = defaultdict(list)
    for embedding, label in zip(embeddings, labels):
        assignments[int(label)].append(embedding.id)

    LOGGER.info("Clearing existing cluster assignments")
    db.execute(update(Claim).values(cluster_id=None))
    db.query(Cluster).delete(synchronize_session=False)
    db.flush()

    created_clusters = 0
    payload_updates: dict[int, int] = {}

    for index, (label, claim_ids) in enumerate(sorted(assignments.items())):
        claim_rows = (
            db.execute(select(Claim).where(Claim.id.in_(claim_ids))).scalars().all()
        )
        if not claim_rows:
            continue

        stats = _aggregate_cluster_stats(claim_rows, index)
        cluster_label = stats.pop("label")
        cluster = Cluster(
            label=cluster_label or f"Cluster {index + 1}",
            num_claims=stats["num_claims"],
            total_cost_usd=stats["total_cost_usd"],
            first_failure_date=stats["first_failure_date"],
            last_failure_date=stats["last_failure_date"],
            sample_dtc_codes=stats["sample_dtc_codes"],
            sample_components=stats["sample_components"],
        )
        db.add(cluster)
        db.flush()

        db.execute(
            update(Claim)
            .where(Claim.id.in_(claim_ids))
            .values(cluster_id=cluster.id)
        )
        for claim_id in claim_ids:
            payload_updates[claim_id] = cluster.id

        created_clusters += 1

    db.commit()
    try:
        vector_store.update_claim_cluster_payload(settings, payload_updates)
    except Exception as exc:  # pragma: no cover - vector DB failures
        LOGGER.warning("Failed to update vector store payloads: %s", exc)

    LOGGER.info("Created %s clusters", created_clusters)
    return created_clusters
