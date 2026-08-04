"""add source metadata and registerable Deep Agents built-in tools

Revision ID: 20260804_04
Revises: 20260804_03
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260804_04"
down_revision = "20260804_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("mcp_catalog_tools", "server_id", existing_type=sa.UUID(), nullable=True, schema="platform")
    op.add_column(
        "mcp_catalog_tools",
        sa.Column("source", sa.String(16), nullable=False, server_default="mcp"),
        schema="platform",
    )
    op.create_index("ix_platform_mcp_catalog_tools_source", "mcp_catalog_tools", ["source"], schema="platform")
    op.create_check_constraint(
        "ck_mcp_catalog_tools_source",
        "mcp_catalog_tools",
        "source IN ('mcp', 'builtin')",
        schema="platform",
    )


def downgrade() -> None:
    op.drop_constraint("ck_mcp_catalog_tools_source", "mcp_catalog_tools", schema="platform")
    op.drop_index("ix_platform_mcp_catalog_tools_source", table_name="mcp_catalog_tools", schema="platform")
    op.drop_column("mcp_catalog_tools", "source", schema="platform")
    op.alter_column("mcp_catalog_tools", "server_id", existing_type=sa.UUID(), nullable=False, schema="platform")
