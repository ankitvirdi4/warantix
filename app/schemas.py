from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .core.security import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class ORMModelMixin:
    """Shared configuration for Pydantic models backed by ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class ClaimBase(BaseModel):
    claim_id: str
    vin: str
    model: str
    model_year: int
    region: Optional[str] = None
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


class ClaimRead(ORMModelMixin, ClaimBase):
    id: int
    embedded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class ClaimsPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ClaimRead]


class ClusterBase(BaseModel):
    label: str
    root_cause_hypothesis: Optional[str] = None
    recommended_actions: Optional[str] = None
    sample_dtc_codes: Optional[str] = None
    sample_components: Optional[str] = None


class ClusterRead(ORMModelMixin, ClusterBase):
    id: int
    num_claims: int
    total_cost_usd: Decimal = Field(..., decimal_places=2)
    first_failure_date: Optional[date] = None
    last_failure_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str | None = None


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class UserRead(ORMModelMixin, UserBase):
    id: int
    role: str
    created_at: datetime | None = None
    last_login: Optional[datetime] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class JobStatus(BaseModel):
    job_id: str
    status: str
    processed: int
    inserted: int
    message: Optional[str] = None
