"""Permission-scoped access to recent messages in the caller's current Feishu group."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from fastmcp.server.dependencies import get_access_token


def _tenant_token() -> str:
    request = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": os.environ["FEISHU_APP_ID"], "app_secret": os.environ["FEISHU_APP_SECRET"]}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read())
    if payload.get("code") != 0:
        raise RuntimeError("Unable to obtain Feishu tenant access token")
    return payload["tenant_access_token"]


def get_current_group_context(limit: int = 30) -> str:
    """Read recent messages only from the Feishu group of the current request.

    The group ID comes from the API-issued MCP JWT rather than an Agent argument,
    so a caller cannot select a different group. Assign this tool only to roles
    permitted to summarize group discussions.
    """
    token = get_access_token()
    claims = token.claims if token else {}
    chat_id = claims.get("feishu_chat_id")
    if not chat_id or claims.get("feishu_chat_type") != "group":
        raise RuntimeError("This tool is available only in the current Feishu group chat")
    if not os.getenv("FEISHU_APP_ID") or not os.getenv("FEISHU_APP_SECRET"):
        raise RuntimeError("FEISHU_APP_ID and FEISHU_APP_SECRET must be configured for this MCP service")
    page_size = max(1, min(int(limit), 100))
    query = urllib.parse.urlencode({"container_id_type": "chat", "container_id": chat_id, "page_size": page_size, "sort_type": "ByCreateTimeDesc"})
    request = urllib.request.Request(
        f"https://open.feishu.cn/open-apis/im/v1/messages?{query}",
        headers={"Authorization": f"Bearer {_tenant_token()}"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read())
    if payload.get("code") != 0:
        raise RuntimeError("Unable to read current group history; verify Feishu message-history permissions")
    lines: list[str] = []
    for item in reversed(payload.get("data", {}).get("items", [])):
        content = item.get("body", {}).get("content", "")
        try:
            parsed = json.loads(content)
            content = parsed.get("text", content) if isinstance(parsed, dict) else content
        except (TypeError, json.JSONDecodeError):
            pass
        if content:
            lines.append(str(content))
    return "\n".join(lines) or "当前群聊没有可用于总结的文本消息。"
