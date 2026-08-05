"""add managed Feishu applications

Revision ID: 20260805_07
Revises: 20260805_06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260805_07"
down_revision = "20260805_06"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "feishu_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("app_id", sa.String(128), nullable=False, unique=True),
        sa.Column("app_secret_ciphertext", sa.Text(), nullable=False),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("desired_state", sa.String(16), nullable=False, server_default="stopped"),
        sa.Column("connection_status", sa.String(16), nullable=False, server_default="stopped"),
        sa.Column("last_error", sa.Text()),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["api_key_id"], ["platform.api_keys.id"], ondelete="RESTRICT"), schema="platform",
    )
    op.create_index("ix_platform_feishu_applications_api_key_id", "feishu_applications", ["api_key_id"], schema="platform")
    op.add_column("feishu_sessions", sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True), schema="platform")
    op.create_foreign_key("fk_feishu_sessions_application_id", "feishu_sessions", "feishu_applications", ["application_id"], ["id"], source_schema="platform", referent_schema="platform", ondelete="SET NULL")
    op.create_index("ix_platform_feishu_sessions_application_id", "feishu_sessions", ["application_id"], schema="platform")
    op.add_column("feishu_active_sessions", sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True), schema="platform")
    op.create_foreign_key("fk_feishu_active_sessions_application_id", "feishu_active_sessions", "feishu_applications", ["application_id"], ["id"], source_schema="platform", referent_schema="platform", ondelete="SET NULL")
    op.create_index("ix_platform_feishu_active_sessions_application_id", "feishu_active_sessions", ["application_id"], schema="platform")
    op.drop_constraint("uq_feishu_session_ordinal", "feishu_sessions", schema="platform", type_="unique")
    op.create_unique_constraint("uq_feishu_session_ordinal", "feishu_sessions", ["application_id", "tenant_key", "open_id", "chat_id", "ordinal"], schema="platform")
    op.drop_constraint("uq_feishu_active_scope", "feishu_active_sessions", schema="platform", type_="unique")
    op.create_unique_constraint("uq_feishu_active_scope", "feishu_active_sessions", ["application_id", "tenant_key", "open_id", "chat_id"], schema="platform")

def downgrade() -> None:
    op.drop_constraint("uq_feishu_active_scope", "feishu_active_sessions", schema="platform", type_="unique")
    op.create_unique_constraint("uq_feishu_active_scope", "feishu_active_sessions", ["tenant_key", "open_id", "chat_id"], schema="platform")
    op.drop_constraint("uq_feishu_session_ordinal", "feishu_sessions", schema="platform", type_="unique")
    op.create_unique_constraint("uq_feishu_session_ordinal", "feishu_sessions", ["tenant_key", "open_id", "chat_id", "ordinal"], schema="platform")
    op.drop_index("ix_platform_feishu_active_sessions_application_id", table_name="feishu_active_sessions", schema="platform")
    op.drop_constraint("fk_feishu_active_sessions_application_id", "feishu_active_sessions", schema="platform", type_="foreignkey")
    op.drop_column("feishu_active_sessions", "application_id", schema="platform")
    op.drop_index("ix_platform_feishu_sessions_application_id", table_name="feishu_sessions", schema="platform")
    op.drop_constraint("fk_feishu_sessions_application_id", "feishu_sessions", schema="platform", type_="foreignkey")
    op.drop_column("feishu_sessions", "application_id", schema="platform")
    op.drop_table("feishu_applications", schema="platform")
