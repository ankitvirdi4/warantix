from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.ingest_service import IngestSummary, ingest_claims_from_csv

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/claims-csv")
def ingest_claims(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type not in ("text/csv", "application/vnd.ms-excel", "application/octet-stream"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    try:
        summary: IngestSummary = ingest_claims_from_csv(db, file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "processed": summary.processed,
        "inserted": summary.inserted,
        "total_cost_usd": float(summary.total_cost_usd),
        "earliest_failure_date": summary.earliest_failure_date,
        "latest_failure_date": summary.latest_failure_date,
    }
