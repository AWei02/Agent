"""add prompt templates and per-Key Feishu prompt profiles

Revision ID: 20260805_06
Revises: 20260804_05
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


revision = "20260805_06"
down_revision = "20260804_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    default_template_id = uuid.uuid4()
    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="platform",
    )
    op.add_column(
        "api_keys",
        sa.Column("prompt_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="platform",
    )
    op.create_foreign_key(
        "fk_api_keys_prompt_template_id",
        "api_keys",
        "prompt_templates",
        ["prompt_template_id"],
        ["id"],
        source_schema="platform",
        referent_schema="platform",
        ondelete="SET NULL",
    )
    op.create_index("ix_platform_api_keys_prompt_template_id", "api_keys", ["prompt_template_id"], schema="platform")
    prompt_templates = sa.table(
        "prompt_templates",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("system_prompt", sa.Text()),
        sa.column("version", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
        schema="platform",
    )
    op.bulk_insert(
        prompt_templates,
        [
            {
                "id": default_template_id,
                "name": "企业知识助手",
                "slug": "knowledge_assistant",
                "description": "迁移自平台原有的知识库助手系统提示词。",
                "system_prompt": "你的角色是企业知识助手。\n当已授权的知识库工具可用且与问题相关时，必须先调用工具，再根据查询结果回答。",
                "version": 1,
                "is_active": True,
            }
        ],
    )
    op.execute(
        sa.text("UPDATE platform.api_keys SET prompt_template_id = :template_id").bindparams(template_id=default_template_id)
    )
    op.create_table(
        "feishu_user_key_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("prompt_profile", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["platform.feishu_user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["api_key_id"], ["platform.api_keys.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "api_key_id", name="uq_feishu_user_key_profile"),
        schema="platform",
    )
    op.create_index("ix_platform_feishu_user_key_profiles_user_id", "feishu_user_key_profiles", ["user_id"], schema="platform")
    op.create_index("ix_platform_feishu_user_key_profiles_api_key_id", "feishu_user_key_profiles", ["api_key_id"], schema="platform")


def downgrade() -> None:
    op.drop_table("feishu_user_key_profiles", schema="platform")
    op.drop_index("ix_platform_api_keys_prompt_template_id", table_name="api_keys", schema="platform")
    op.drop_constraint("fk_api_keys_prompt_template_id", "api_keys", schema="platform", type_="foreignkey")
    op.drop_column("api_keys", "prompt_template_id", schema="platform")
    op.drop_table("prompt_templates", schema="platform")
