from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..database import get_db
from ..services.ai_reasoning_service import update_ai_explanations_for_all_clusters
from ..services.clustering_service import recalculate_clusters
from ..services.embedding_service import embed_new_claims

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/recluster")
def run_full_recluster(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    embedded = embed_new_claims(db, settings)
    clusters_created = recalculate_clusters(db, settings)
    ai_updated = update_ai_explanations_for_all_clusters(db, settings)

    return {
        "embedded": embedded,
        "clusters_created": clusters_created,
        "clusters_updated_with_ai": ai_updated,
    }
