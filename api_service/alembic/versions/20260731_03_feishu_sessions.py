"""add persistent Feishu conversation directory

Revision ID: 20260731_03
Revises: 20260731_02
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260731_03"
down_revision = "20260731_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feishu_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_key", sa.String(128), nullable=False),
        sa.Column("open_id", sa.String(128), nullable=False),
        sa.Column("chat_id", sa.String(128), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("thread_id", sa.String(512), nullable=False, unique=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_key", "open_id", "chat_id", "ordinal", name="uq_feishu_session_ordinal"),
        schema="platform",
    )
    op.create_index("ix_platform_feishu_sessions_tenant_key", "feishu_sessions", ["tenant_key"], schema="platform")
    op.create_index("ix_platform_feishu_sessions_open_id", "feishu_sessions", ["open_id"], schema="platform")
    op.create_index("ix_platform_feishu_sessions_chat_id", "feishu_sessions", ["chat_id"], schema="platform")
    op.create_index("ix_platform_feishu_sessions_is_archived", "feishu_sessions", ["is_archived"], schema="platform")
    op.create_table(
        "feishu_active_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_key", sa.String(128), nullable=False),
        sa.Column("open_id", sa.String(128), nullable=False),
        sa.Column("chat_id", sa.String(128), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["platform.feishu_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_key", "open_id", "chat_id", name="uq_feishu_active_scope"),
        schema="platform",
    )


def downgrade() -> None:
    op.drop_table("feishu_active_sessions", schema="platform")
    op.drop_index("ix_platform_feishu_sessions_is_archived", table_name="feishu_sessions", schema="platform")
    op.drop_index("ix_platform_feishu_sessions_chat_id", table_name="feishu_sessions", schema="platform")
    op.drop_index("ix_platform_feishu_sessions_open_id", table_name="feishu_sessions", schema="platform")
    op.drop_index("ix_platform_feishu_sessions_tenant_key", table_name="feishu_sessions", schema="platform")
    op.drop_table("feishu_sessions", schema="platform")
