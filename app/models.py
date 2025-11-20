from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    label: Mapped[str] = mapped_column(String(255))
    root_cause_hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_dtc_codes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_components: Mapped[str | None] = mapped_column(Text, nullable=True)
    num_claims: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    first_failure_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_failure_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    claims: Mapped[list["Claim"]] = relationship("Claim", back_populates="cluster")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    claim_id: Mapped[str] = mapped_column(String(255), index=True)
    vin: Mapped[str] = mapped_column(String(255), index=True)
    model: Mapped[str] = mapped_column(String(255))
    model_year: Mapped[int] = mapped_column(Integer)
    region: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    mileage_km: Mapped[int] = mapped_column(Integer)
    failure_date: Mapped[date] = mapped_column(Date)
    component: Mapped[str] = mapped_column(String(255), index=True)
    part_number: Mapped[str] = mapped_column(String(255))
    dtc_codes: Mapped[str] = mapped_column(Text)
    symptom_text: Mapped[str] = mapped_column(Text)
    repair_action: Mapped[str] = mapped_column(Text)
    claim_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    dealer_id: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id"), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cluster: Mapped[Cluster | None] = relationship("Cluster", back_populates="claims")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
