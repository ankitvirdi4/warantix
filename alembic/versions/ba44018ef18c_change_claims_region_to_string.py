"""Change claims.region to string

Revision ID: ba44018ef18c
Revises: 20240701_add_claim_embedded_at
Create Date: 2024-10-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ba44018ef18c"
down_revision = "20240701_add_claim_embedded_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "claims",
        "region",
        existing_type=sa.Float(),
        type_=sa.String(length=16),
        existing_nullable=False,
        nullable=True,
        postgresql_using="region::text",
    )


def downgrade() -> None:
    op.alter_column(
        "claims",
        "region",
        existing_type=sa.String(length=16),
        type_=sa.Float(),
        existing_nullable=True,
        nullable=False,
        postgresql_using="region::double precision",
    )
