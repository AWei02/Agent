"""add per-key final output JSON Schema

Revision ID: 20260805_10
Revises: 20260805_09
"""

from alembic import op
import sqlalchemy as sa


revision = "20260805_10"
down_revision = "20260805_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("output_schema", sa.JSON(), nullable=True), schema="platform")


def downgrade() -> None:
    op.drop_column("api_keys", "output_schema", schema="platform")
