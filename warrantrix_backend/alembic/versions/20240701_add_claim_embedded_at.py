"""Add embedded_at column to claims

Revision ID: 20240701_add_claim_embedded_at
Revises: 
Create Date: 2024-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240701_add_claim_embedded_at"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("claims", sa.Column("embedded_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("claims", "embedded_at")
