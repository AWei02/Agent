"""add Feishu user policy and conversation audit tables

Revision ID: 20260731_04
Revises: 20260731_03
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260731_04"
down_revision = "20260731_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feishu_user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_key", sa.String(128), nullable=False), sa.Column("open_id", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False), sa.Column("avatar_url", sa.String(2048)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_key", "open_id", name="uq_feishu_user_identity"), schema="platform",
    )
    op.create_table("feishu_user_roles", sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("role_id", postgresql.UUID(as_uuid=True), primary_key=True), sa.ForeignKeyConstraint(["user_id"], ["platform.feishu_user_profiles.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["role_id"], ["platform.rbac_roles.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id", "role_id", name="uq_feishu_user_role"), schema="platform")
    op.create_table("feishu_user_tool_permissions", sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("tool_id", postgresql.UUID(as_uuid=True), primary_key=True), sa.ForeignKeyConstraint(["user_id"], ["platform.feishu_user_profiles.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["tool_id"], ["platform.mcp_catalog_tools.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id", "tool_id", name="uq_feishu_user_tool"), schema="platform")
    op.create_table("feishu_turns", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("request_messages", sa.JSON(), nullable=False), sa.Column("response_content", sa.Text()), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.ForeignKeyConstraint(["session_id"], ["platform.feishu_sessions.id"], ondelete="CASCADE"), schema="platform")
    op.create_index("ix_platform_feishu_turns_session_id", "feishu_turns", ["session_id"], schema="platform")


def downgrade() -> None:
    op.drop_table("feishu_turns", schema="platform")
    op.drop_table("feishu_user_tool_permissions", schema="platform")
    op.drop_table("feishu_user_roles", schema="platform")
    op.drop_table("feishu_user_profiles", schema="platform")
