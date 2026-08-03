"""create core API-key, RBAC, and MCP catalog tables

Revision ID: 20260731_01
Revises:
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260731_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")
    op.execute("CREATE SCHEMA IF NOT EXISTS langgraph")

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("key_prefix", sa.String(24), nullable=False, unique=True),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("file_access", sa.String(16), nullable=False, server_default="none"),
        sa.Column("notes", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="platform",
    )
    op.create_table(
        "rbac_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="platform",
    )
    op.create_table(
        "mcp_servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="platform",
    )
    op.create_table(
        "mcp_catalog_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("server_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("input_schema", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["server_id"], ["platform.mcp_servers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("server_id", "name", name="uq_mcp_catalog_tools_server_name"),
        schema="platform",
    )
    op.create_index("ix_platform_mcp_catalog_tools_server_id", "mcp_catalog_tools", ["server_id"], schema="platform")
    op.create_table(
        "rbac_role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["platform.rbac_roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["platform.mcp_catalog_tools.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("role_id", "tool_id", name="uq_rbac_role_permissions_role_tool"),
        schema="platform",
    )
    op.create_table(
        "api_key_roles",
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["api_key_id"], ["platform.api_keys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["platform.rbac_roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("api_key_id", "role_id", name="uq_api_key_roles_key_role"),
        schema="platform",
    )


def downgrade() -> None:
    op.drop_table("api_key_roles", schema="platform")
    op.drop_table("rbac_role_permissions", schema="platform")
    op.drop_index("ix_platform_mcp_catalog_tools_server_id", table_name="mcp_catalog_tools", schema="platform")
    op.drop_table("mcp_catalog_tools", schema="platform")
    op.drop_table("mcp_servers", schema="platform")
    op.drop_table("rbac_roles", schema="platform")
    op.drop_table("api_keys", schema="platform")
