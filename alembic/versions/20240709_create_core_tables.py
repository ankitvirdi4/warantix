"""Create core tables for clusters, claims, and users

Revision ID: 20240709_create_core_tables
Revises: 
Create Date: 2024-07-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20240709_create_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("root_cause_hypothesis", sa.Text(), nullable=True),
        sa.Column("recommended_actions", sa.Text(), nullable=True),
        sa.Column("sample_dtc_codes", sa.Text(), nullable=True),
        sa.Column("sample_components", sa.Text(), nullable=True),
        sa.Column("num_claims", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "total_cost_usd",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("first_failure_date", sa.Date(), nullable=True),
        sa.Column("last_failure_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_login", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_id", sa.String(length=255), nullable=False),
        sa.Column("vin", sa.String(length=255), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("model_year", sa.Integer(), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=False),
        sa.Column("mileage_km", sa.Integer(), nullable=False),
        sa.Column("failure_date", sa.Date(), nullable=False),
        sa.Column("component", sa.String(length=255), nullable=False),
        sa.Column("part_number", sa.String(length=255), nullable=False),
        sa.Column("dtc_codes", sa.Text(), nullable=False),
        sa.Column("symptom_text", sa.Text(), nullable=False),
        sa.Column("repair_action", sa.Text(), nullable=False),
        sa.Column("claim_cost_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("dealer_id", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"]),
    )
    op.create_index("ix_claims_claim_id", "claims", ["claim_id"], unique=False)
    op.create_index("ix_claims_vin", "claims", ["vin"], unique=False)
    op.create_index("ix_claims_region", "claims", ["region"], unique=False)
    op.create_index("ix_claims_component", "claims", ["component"], unique=False)
    op.create_index("ix_claims_cluster_id", "claims", ["cluster_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_claims_cluster_id", table_name="claims")
    op.drop_index("ix_claims_component", table_name="claims")
    op.drop_index("ix_claims_region", table_name="claims")
    op.drop_index("ix_claims_vin", table_name="claims")
    op.drop_index("ix_claims_claim_id", table_name="claims")
    op.drop_table("claims")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_table("clusters")
