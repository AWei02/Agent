"""add API-key chat tracking and audit tables

Revision ID: 20260731_02
Revises: 20260731_01
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260731_02"
down_revision = "20260731_01"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("api_keys", sa.Column("chat_tracking", sa.Boolean(), nullable=False, server_default=sa.false()), schema="platform")
    op.create_table("api_audit_sessions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("api_key_id", postgresql.UUID(as_uuid=True)), sa.Column("api_key_name", sa.String(120), nullable=False), sa.Column("thread_id", sa.String(512), nullable=False, unique=True), sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.ForeignKeyConstraint(["api_key_id"], ["platform.api_keys.id"], ondelete="SET NULL"), schema="platform")
    op.create_index("ix_platform_api_audit_sessions_api_key_id", "api_audit_sessions", ["api_key_id"], schema="platform")
    op.create_table("api_audit_turns", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("request_messages", sa.JSON(), nullable=False), sa.Column("response_content", sa.Text()), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.ForeignKeyConstraint(["session_id"], ["platform.api_audit_sessions.id"], ondelete="CASCADE"), schema="platform")
    op.create_index("ix_platform_api_audit_turns_session_id", "api_audit_turns", ["session_id"], schema="platform")

def downgrade() -> None:
    op.drop_table("api_audit_turns", schema="platform")
    op.drop_table("api_audit_sessions", schema="platform")
    op.drop_column("api_keys", "chat_tracking", schema="platform")
