from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analytics_service import get_cost_by_component, get_top_failure_clusters

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-failures")
def top_failures(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    records = get_top_failure_clusters(db, limit=limit)
    return {"clusters": [dict(record) for record in records]}


@router.get("/cost-by-component")
def cost_by_component(db: Session = Depends(get_db)):
    records = get_cost_by_component(db)
    return [dict(record) for record in records]
