"""store Feishu private/group chat type

Revision ID: 20260731_05
Revises: 20260731_04
"""
from alembic import op
import sqlalchemy as sa

revision = "20260731_05"
down_revision = "20260731_04"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("feishu_sessions", sa.Column("chat_type", sa.String(16), nullable=False, server_default="unknown"), schema="platform")

def downgrade() -> None:
    op.drop_column("feishu_sessions", "chat_type", schema="platform")
