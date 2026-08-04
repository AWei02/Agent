"""retain API-key values for the protected single-admin console

Revision ID: 20260804_03
Revises: 20260803_06
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260804_03"
down_revision = "20260803_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable preserves existing rows, whose original plaintext cannot be
    # reconstructed from the stored SHA-256 hash.
    op.add_column("api_keys", sa.Column("key_value", sa.Text(), nullable=True), schema="platform")


def downgrade() -> None:
    op.drop_column("api_keys", "key_value", schema="platform")
