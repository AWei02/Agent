"""Add reversible visibility to tracked API sessions.

Revision ID: 20260803_06
Revises: 20260731_05
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260803_06"
down_revision = "20260731_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_audit_sessions",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="platform",
    )
    op.create_index(
        "ix_platform_api_audit_sessions_is_archived",
        "api_audit_sessions",
        ["is_archived"],
        schema="platform",
    )
    op.alter_column("api_audit_sessions", "is_archived", server_default=None, schema="platform")


def downgrade() -> None:
    op.drop_index("ix_platform_api_audit_sessions_is_archived", table_name="api_audit_sessions", schema="platform")
    op.drop_column("api_audit_sessions", "is_archived", schema="platform")
