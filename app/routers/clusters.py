from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Claim, Cluster
from ..schemas import ClusterRead

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=list[ClusterRead])
def list_clusters(
    sort_by: Optional[str] = Query(None, pattern="^(cost|count)$"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Cluster)

    if sort_by == "cost":
        stmt = stmt.order_by(Cluster.total_cost_usd.desc())
    elif sort_by == "count":
        stmt = stmt.order_by(Cluster.num_claims.desc())
    else:
        stmt = stmt.order_by(Cluster.id.asc())

    if limit:
        stmt = stmt.limit(limit)

    clusters = db.execute(stmt).scalars().all()
    return [ClusterRead.from_orm(cluster) for cluster in clusters]


@router.get("/{cluster_id}", response_model=ClusterRead)
def get_cluster(cluster_id: int, db: Session = Depends(get_db)) -> ClusterRead:
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    if cluster.num_claims == 0:
        agg_stmt = (
            select(
                func.count(Claim.id).label("num_claims"),
                func.coalesce(func.sum(Claim.claim_cost_usd), 0).label("total_cost_usd"),
            )
            .where(Claim.cluster_id == cluster_id)
        )
        agg = db.execute(agg_stmt).one()
        cluster.num_claims = agg.num_claims
        cluster.total_cost_usd = agg.total_cost_usd

    return ClusterRead.from_orm(cluster)
