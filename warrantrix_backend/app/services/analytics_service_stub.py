from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Claim, Cluster


def get_top_failure_clusters(db: Session, limit: int = 5):
    stmt = (
        select(
            Cluster.id.label("cluster_id"),
            Cluster.label,
            func.count(Claim.id).label("num_claims"),
            func.coalesce(func.sum(Claim.claim_cost_usd), 0).label("total_cost_usd"),
        )
        .join(Claim, Claim.cluster_id == Cluster.id, isouter=True)
        .group_by(Cluster.id)
        .order_by(func.count(Claim.id).desc())
        .limit(limit)
    )
    return db.execute(stmt).mappings().all()


def get_cost_by_component(db: Session):
    stmt = (
        select(
            Claim.component,
            func.count(Claim.id).label("claim_count"),
            func.coalesce(func.sum(Claim.claim_cost_usd), 0).label("total_cost_usd"),
        )
        .group_by(Claim.component)
        .order_by(func.coalesce(func.sum(Claim.claim_cost_usd), 0).desc())
    )
    return db.execute(stmt).mappings().all()
