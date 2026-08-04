"""Business tables owned by the platform schema."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, MetaData, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import get_settings


class Base(DeclarativeBase):
    metadata = MetaData(schema=get_settings().database_schema)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    # This console is deliberately single-admin: retain the generated value so it
    # can be retrieved later from the protected administration interface.
    key_value: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    file_access: Mapped[str] = mapped_column(String(16), default="none", nullable=False)
    chat_tracking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list["ApiKeyRole"]] = relationship(back_populates="api_key", cascade="all, delete-orphan")


class RbacRole(TimestampMixin, Base):
    __tablename__ = "rbac_roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    permissions: Mapped[list["RbacRolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["ApiKeyRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class McpServer(TimestampMixin, Base):
    __tablename__ = "mcp_servers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tools: Mapped[list["McpCatalogTool"]] = relationship(back_populates="server", cascade="all, delete-orphan")


class McpCatalogTool(TimestampMixin, Base):
    __tablename__ = "mcp_catalog_tools"
    __table_args__ = (UniqueConstraint("server_id", "name", name="uq_mcp_catalog_tools_server_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform.mcp_servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    input_schema: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    server: Mapped[McpServer] = relationship(back_populates="tools")
    role_permissions: Mapped[list["RbacRolePermission"]] = relationship(
        back_populates="tool", cascade="all, delete-orphan"
    )


class RbacRolePermission(Base):
    __tablename__ = "rbac_role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "tool_id", name="uq_rbac_role_permissions_role_tool"),)

    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform.rbac_roles.id", ondelete="CASCADE"), primary_key=True
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform.mcp_catalog_tools.id", ondelete="CASCADE"), primary_key=True
    )

    role: Mapped[RbacRole] = relationship(back_populates="permissions")
    tool: Mapped[McpCatalogTool] = relationship(back_populates="role_permissions")


class ApiKeyRole(Base):
    __tablename__ = "api_key_roles"
    __table_args__ = (UniqueConstraint("api_key_id", "role_id", name="uq_api_key_roles_key_role"),)

    api_key_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform.api_keys.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform.rbac_roles.id", ondelete="CASCADE"), primary_key=True
    )

    api_key: Mapped[ApiKey] = relationship(back_populates="roles")
    role: Mapped[RbacRole] = relationship(back_populates="api_keys")


class ApiAuditSession(TimestampMixin, Base):
    __tablename__ = "api_audit_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("platform.api_keys.id", ondelete="SET NULL"), index=True)
    api_key_name: Mapped[str] = mapped_column(String(120), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ApiAuditTurn(Base):
    __tablename__ = "api_audit_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("platform.api_audit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    request_messages: Mapped[list] = mapped_column(JSON, nullable=False)
    response_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FeishuSession(TimestampMixin, Base):
    """A user-selectable conversation directory entry for one Feishu chat."""

    __tablename__ = "feishu_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_key", "open_id", "chat_id", "ordinal", name="uq_feishu_session_ordinal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    open_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    chat_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    chat_type: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FeishuActiveSession(Base):
    """The selected session for a Feishu user within one chat."""

    __tablename__ = "feishu_active_sessions"
    __table_args__ = (UniqueConstraint("tenant_key", "open_id", "chat_id", name="uq_feishu_active_scope"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=False)
    open_id: Mapped[str] = mapped_column(String(128), nullable=False)
    chat_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform.feishu_sessions.id", ondelete="CASCADE"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class FeishuUserProfile(TimestampMixin, Base):
    """A Feishu principal whose incremental permissions are managed in the console."""

    __tablename__ = "feishu_user_profiles"
    __table_args__ = (UniqueConstraint("tenant_key", "open_id", name="uq_feishu_user_identity"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=False)
    open_id: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FeishuUserRole(Base):
    __tablename__ = "feishu_user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_feishu_user_role"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("platform.feishu_user_profiles.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("platform.rbac_roles.id", ondelete="CASCADE"), primary_key=True)


class FeishuUserToolPermission(Base):
    __tablename__ = "feishu_user_tool_permissions"
    __table_args__ = (UniqueConstraint("user_id", "tool_id", name="uq_feishu_user_tool"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("platform.feishu_user_profiles.id", ondelete="CASCADE"), primary_key=True)
    tool_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("platform.mcp_catalog_tools.id", ondelete="CASCADE"), primary_key=True)


class FeishuTurn(Base):
    __tablename__ = "feishu_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("platform.feishu_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    request_messages: Mapped[list] = mapped_column(JSON, nullable=False)
    response_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
