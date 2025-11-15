from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Claim
from ..schemas import ClaimRead, ClaimsPage

router = APIRouter(prefix="/claims", tags=["claims"])


def apply_filters(query, model: Optional[str], region: Optional[str], component: Optional[str], cluster_id: Optional[int], date_from: Optional[date], date_to: Optional[date]):
    conditions = []
    if model:
        conditions.append(Claim.model == model)
    if region:
        conditions.append(Claim.region == region)
    if component:
        conditions.append(Claim.component == component)
    if cluster_id is not None:
        conditions.append(Claim.cluster_id == cluster_id)
    if date_from:
        conditions.append(Claim.failure_date >= date_from)
    if date_to:
        conditions.append(Claim.failure_date <= date_to)

    if conditions:
        query = query.where(and_(*conditions))
    return query


@router.get("", response_model=ClaimsPage)
def list_claims(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    model: Optional[str] = None,
    region: Optional[str] = None,
    component: Optional[str] = None,
    cluster_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
) -> ClaimsPage:
    base_query = select(Claim)
    base_query = apply_filters(base_query, model, region, component, cluster_id, date_from, date_to)

    total_query = base_query.with_only_columns(func.count()).order_by(None)
    total = db.execute(total_query).scalar_one()

    result = db.execute(
        base_query.order_by(Claim.failure_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()

    return ClaimsPage(
        total=total,
        page=page,
        page_size=page_size,
        items=[ClaimRead.from_orm(item) for item in items],
    )


@router.get("/{claim_id}", response_model=ClaimRead)
def get_claim(claim_id: int, db: Session = Depends(get_db)) -> ClaimRead:
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return ClaimRead.from_orm(claim)
