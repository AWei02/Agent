"""Short-lived MCP JWT issuance; only the API service should mint these tokens."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import jwt

from app.services.api_keys import AuthorizedSubject, GrantedTool


def issue_mcp_token(subject: AuthorizedSubject, *, audience: str, tools: list[GrantedTool], context: dict[str, str] | None = None) -> str:
    secret = os.getenv("MCP_AUTH_SECRET", "")
    if not secret:
        raise RuntimeError("MCP_AUTH_SECRET must be configured")
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject.api_key_id),
        "tools": [tool.name for tool in tools],
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "iss": "deep-agents-api",
        "aud": audience,
    }
    if context:
        payload.update({key: value for key, value in context.items() if value})
    return jwt.encode(payload, secret, algorithm="HS256")
