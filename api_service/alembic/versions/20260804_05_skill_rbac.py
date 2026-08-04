"""add skill catalog and RBAC grants

Revision ID: 20260804_05
Revises: 20260804_04
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260804_05"
down_revision = "20260804_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("path", sa.String(512), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="platform",
    )
    op.create_table(
        "rbac_role_skills",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.ForeignKeyConstraint(["role_id"], ["platform.rbac_roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["platform.skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("role_id", "skill_id", name="uq_rbac_role_skills_role_skill"),
        schema="platform",
    )
    op.create_table(
        "feishu_user_skill_permissions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.ForeignKeyConstraint(["user_id"], ["platform.feishu_user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["platform.skills.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_feishu_user_skill"),
        schema="platform",
    )


def downgrade() -> None:
    op.drop_table("feishu_user_skill_permissions", schema="platform")
    op.drop_table("rbac_role_skills", schema="platform")
    op.drop_table("skills", schema="platform")
