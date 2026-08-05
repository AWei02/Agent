"""scope Feishu users to their managed application

Revision ID: 20260805_08
Revises: 20260805_07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260805_08"
down_revision = "20260805_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "feishu_user_profiles",
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="platform",
    )
    op.create_foreign_key(
        "fk_feishu_user_profiles_application_id",
        "feishu_user_profiles",
        "feishu_applications",
        ["application_id"],
        ["id"],
        source_schema="platform",
        referent_schema="platform",
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_platform_feishu_user_profiles_application_id",
        "feishu_user_profiles",
        ["application_id"],
        schema="platform",
    )
    op.drop_constraint("uq_feishu_user_identity", "feishu_user_profiles", schema="platform", type_="unique")
    op.create_unique_constraint(
        "uq_feishu_user_identity",
        "feishu_user_profiles",
        ["application_id", "tenant_key", "open_id"],
        schema="platform",
    )


def downgrade() -> None:
    op.drop_constraint("uq_feishu_user_identity", "feishu_user_profiles", schema="platform", type_="unique")
    op.create_unique_constraint(
        "uq_feishu_user_identity",
        "feishu_user_profiles",
        ["tenant_key", "open_id"],
        schema="platform",
    )
    op.drop_index(
        "ix_platform_feishu_user_profiles_application_id",
        table_name="feishu_user_profiles",
        schema="platform",
    )
    op.drop_constraint(
        "fk_feishu_user_profiles_application_id",
        "feishu_user_profiles",
        schema="platform",
        type_="foreignkey",
    )
    op.drop_column("feishu_user_profiles", "application_id", schema="platform")
