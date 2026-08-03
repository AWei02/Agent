"""JWT verification and per-tool authorization for the MCP boundary."""

from __future__ import annotations

import os
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastmcp.server.auth import AccessToken, AuthContext, TokenVerifier

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class McpJwtVerifier(TokenVerifier):
    """Accept only short-lived JWTs minted by the API service."""

    def __init__(self) -> None:
        self.secret = os.environ.get("MCP_AUTH_SECRET", "")
        self.audience = os.environ.get("MCP_AUTH_AUDIENCE", "")
        if not self.secret or not self.audience:
            raise RuntimeError("MCP_AUTH_SECRET and MCP_AUTH_AUDIENCE must be configured")
        super().__init__()

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                audience=self.audience,
                issuer="deep-agents-api",
                options={"require": ["sub", "tools", "exp", "iss", "aud"]},
            )
            tools = claims["tools"]
            if not isinstance(tools, list) or not all(isinstance(tool, str) for tool in tools):
                return None
            return AccessToken(token=token, client_id=str(claims["sub"]), scopes=tools, claims=claims)
        except jwt.InvalidTokenError:
            return None


def may_use_tool(context: AuthContext) -> bool:
    """Used on both tools/list and tools/call by FastMCP's AuthMiddleware."""
    if context.token is None:
        return False
    granted_tools = context.token.claims.get("tools", [])
    return "*" in granted_tools or context.component.name in granted_tools
