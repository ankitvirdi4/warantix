from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ClaimBase(BaseModel):
    claim_id: str
    vin: str
    model: str
    model_year: int
    region: str
    mileage_km: int
    failure_date: date
    component: str
    part_number: str
    dtc_codes: str
    symptom_text: str
    repair_action: str
    claim_cost_usd: Decimal = Field(..., decimal_places=2)
    dealer_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cluster_id: Optional[int] = None


class ClaimCreate(ClaimBase):
    pass


class ClaimRead(ClaimBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ClaimsPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ClaimRead]


class ClusterBase(BaseModel):
    label: str
    root_cause_hypothesis: Optional[str] = None
    recommended_actions: Optional[str] = None
    sample_dtc_codes: Optional[str] = None
    sample_components: Optional[str] = None


class ClusterRead(ClusterBase):
    id: int
    num_claims: int
    total_cost_usd: Decimal = Field(..., decimal_places=2)
    first_failure_date: Optional[date] = None
    last_failure_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    name: str
    role: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


class JobStatus(BaseModel):
    job_id: str
    status: str
    processed: int
    inserted: int
    message: Optional[str] = None
