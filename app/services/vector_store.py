from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from ..config import Settings

LOGGER = logging.getLogger(__name__)

COLLECTION_NAME = "claim_embeddings"
OPENAI_EMBEDDING_DIM = 1536


@lru_cache(maxsize=1)
def _get_client(url: str, api_key: Optional[str]) -> QdrantClient:
    return QdrantClient(url=url, api_key=api_key)


def get_client(settings: Settings) -> QdrantClient:
    return _get_client(settings.qdrant_url, settings.qdrant_api_key)


@dataclass(slots=True)
class ClaimEmbedding:
    id: int
    vector: list[float]
    payload: dict


def init_vector_store(settings: Settings) -> None:
    client = get_client(settings)
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        return
    except Exception:  # pragma: no cover - qdrant raises client-specific errors
        LOGGER.info("Creating Qdrant collection '%s'", COLLECTION_NAME)

    vectors_config = qmodels.VectorParams(
        size=OPENAI_EMBEDDING_DIM,
        distance=qmodels.Distance.COSINE,
    )
    try:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=vectors_config,
        )
    except Exception as exc:  # pragma: no cover - collection may already exist
        LOGGER.warning("Failed to create collection '%s': %s", COLLECTION_NAME, exc)


def upsert_claim_embeddings(settings: Settings, claim_vectors: Iterable[ClaimEmbedding]) -> None:
    claim_vectors = list(claim_vectors)
    if not claim_vectors:
        return

    init_vector_store(settings)
    client = get_client(settings)
    points = [
        qmodels.PointStruct(
            id=embedding.id,
            vector=embedding.vector,
            payload=embedding.payload,
        )
        for embedding in claim_vectors
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def query_similar_claims(
    settings: Settings,
    vector: list[float],
    limit: int = 10,
    filter: Optional[dict] = None,
) -> list[dict]:
    client = get_client(settings)
    qdrant_filter = None
    if filter:
        if isinstance(filter, qmodels.Filter):
            qdrant_filter = filter
        else:
            qdrant_filter = qmodels.Filter(**filter)

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=limit,
        with_payload=True,
        filter=qdrant_filter,
    )

    return [
        {
            "id": point.id,
            "score": point.score,
            "payload": point.payload or {},
        }
        for point in results
    ]


def fetch_all_embeddings(settings: Settings) -> list[ClaimEmbedding]:
    client = get_client(settings)
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
    except Exception:
        LOGGER.info("Vector collection '%s' not initialised yet", COLLECTION_NAME)
        return []
    result: list[ClaimEmbedding] = []
    offset = None

    while True:
        scroll_result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            with_payload=True,
            with_vectors=True,
            offset=offset,
        )
        if isinstance(scroll_result, tuple):
            points, offset = scroll_result
        else:  # pragma: no cover - newer client versions return objects
            points = scroll_result.points
            offset = scroll_result.next_page_offset
        if not points:
            break
        for point in points:
            result.append(
                ClaimEmbedding(
                    id=int(point.id),
                    vector=list(point.vector),
                    payload=point.payload or {},
                )
            )
        if offset is None:
            break

    return result


def update_claim_cluster_payload(settings: Settings, assignments: dict[int, int]) -> None:
    if not assignments:
        return

    client = get_client(settings)
    for claim_id, cluster_id in assignments.items():
        client.set_payload(
            collection_name=COLLECTION_NAME,
            payload={"cluster_id": cluster_id},
            points=[claim_id],
        )
