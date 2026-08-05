"""add durable Feishu background generation tasks

Revision ID: 20260805_09
Revises: 20260805_08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260805_09"
down_revision = "20260805_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feishu_generation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("result_content", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["application_id"], ["platform.feishu_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["platform.feishu_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["api_key_id"], ["platform.api_keys.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["platform.feishu_user_profiles.id"], ondelete="CASCADE"),
        schema="platform",
    )
    for column in ("application_id", "session_id", "api_key_id", "user_id", "status"):
        op.create_index(f"ix_platform_feishu_generation_tasks_{column}", "feishu_generation_tasks", [column], schema="platform")


def downgrade() -> None:
    op.drop_table("feishu_generation_tasks", schema="platform")
