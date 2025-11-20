from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from io import StringIO

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..models import Claim


@dataclass
class IngestSummary:
    processed: int
    inserted: int
    total_cost_usd: Decimal
    earliest_failure_date: date | None
    latest_failure_date: date | None


CSV_COLUMNS = [
    "claim_id",
    "vin",
    "model",
    "model_year",
    "region",
    "mileage_km",
    "failure_date",
    "component",
    "part_number",
    "dtc_codes",
    "symptom_text",
    "repair_action",
    "claim_cost_usd",
    "dealer_id",
    "latitude",
    "longitude",
]


def ingest_claims_from_csv(db: Session, file: UploadFile) -> IngestSummary:
    file.file.seek(0)
    raw_data = file.file.read()
    df = pd.read_csv(StringIO(raw_data.decode("utf-8")))

    missing_cols = [col for col in CSV_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in CSV: {', '.join(missing_cols)}")

    df = df[CSV_COLUMNS]
    df["region"] = df["region"].apply(lambda value: str(value) if pd.notna(value) else None)
    processed = len(df.index)

    df["failure_date"] = pd.to_datetime(df["failure_date"]).dt.date
    df["claim_cost_usd"] = df["claim_cost_usd"].astype(float)

    earliest_failure_date: date | None = None
    latest_failure_date: date | None = None
    total_cost = Decimal("0")

    inserted = 0
    for record in df.to_dict(orient="records"):
        claim = Claim(
            claim_id=record["claim_id"],
            vin=record["vin"],
            model=record["model"],
            model_year=int(record["model_year"]),
            region=record["region"],
            mileage_km=int(record["mileage_km"]),
            failure_date=record["failure_date"],
            component=record["component"],
            part_number=record["part_number"],
            dtc_codes=record["dtc_codes"],
            symptom_text=record["symptom_text"],
            repair_action=record["repair_action"],
            claim_cost_usd=Decimal(str(record["claim_cost_usd"])),
            dealer_id=record["dealer_id"],
            latitude=float(record["latitude"]) if pd.notna(record["latitude"]) else None,
            longitude=float(record["longitude"]) if pd.notna(record["longitude"]) else None,
        )
        db.add(claim)
        inserted += 1
        total_cost += Decimal(str(record["claim_cost_usd"]))

        failure_date = record["failure_date"]
        if failure_date:
            if earliest_failure_date is None or failure_date < earliest_failure_date:
                earliest_failure_date = failure_date
            if latest_failure_date is None or failure_date > latest_failure_date:
                latest_failure_date = failure_date

    db.commit()

    return IngestSummary(
        processed=processed,
        inserted=inserted,
        total_cost_usd=total_cost,
        earliest_failure_date=earliest_failure_date,
        latest_failure_date=latest_failure_date,
    )
