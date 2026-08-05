"""Request-scoped Deep Agent construction with only the caller's granted tools."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
import logging
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends.state import StateBackend
from langchain.agents.middleware import ModelRequest, ModelResponse, TodoListMiddleware, wrap_model_call, wrap_tool_call
from langchain_core.messages import ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.services.api_keys import AuthorizedSubject, GrantedTool, apply_file_access_cap
from app.services.builtin_tools import BUILTIN_TOOL_NAMES
from app.services.mcp_tokens import issue_mcp_token
from app.services.skills import GrantedSkill, resolve_skill_path


class AgentRuntimeError(RuntimeError):
    """An upstream model or MCP connection could not be prepared."""


SKILL_VIRTUAL_ROOT = "/skills"
logger = logging.getLogger(__name__)


def build_skill_files(skills: list[GrantedSkill] | None) -> dict[str, dict[str, str]]:
    """Load only granted on-disk skills into the request's virtual filesystem.

    ``create_deep_agent`` uses ``StateBackend`` by default.  Passing a Windows
    directory to ``skills=`` therefore does not make that directory readable by
    the agent.  We stage the authorized skill directories in state instead,
    where the Skills middleware can discover and progressively read them.
    """
    files: dict[str, dict[str, str]] = {}
    for skill in skills or []:
        root = resolve_skill_path(skill.path)
        # The skills middleware scans one level below its source path.  The
        # catalog name is stable and gives every granted skill an isolated
        # virtual directory, including skills stored in nested folders.
        virtual_dir = f"{SKILL_VIRTUAL_ROOT}/{skill.name}"
        for source in root.rglob("*"):
            if not source.is_file():
                continue
            try:
                relative = source.relative_to(root).as_posix()
                files[f"{virtual_dir}/{relative}"] = {"content": source.read_text(encoding="utf-8")}
            except UnicodeDecodeError:
                # StateBackend transports text.  Binary references (PDFs,
                # images, archives) are optional supporting material and must
                # not prevent the Skill.md instructions from being usable.
                logger.warning("Skipping non-UTF-8 skill asset: %s", source)
            except OSError as exc:
                raise AgentRuntimeError(f"Unable to read granted skill '{skill.name}'") from exc
    return files


def _connections_for(subject: AuthorizedSubject, tools: list[GrantedTool], context: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    tools_by_server: dict[tuple[str, str], list[GrantedTool]] = defaultdict(list)
    for tool in tools:
        if tool.source != "mcp" or not tool.server_name or not tool.server_url:
            continue
        tools_by_server[(tool.server_name, tool.server_url)].append(tool)

    connections: dict[str, dict[str, Any]] = {}
    for index, ((server_name, server_url), server_tools) in enumerate(tools_by_server.items(), start=1):
        connection_name = f"{server_name}-{index}"
        token = issue_mcp_token(subject, audience=server_url, tools=server_tools, context=context)
        connections[connection_name] = {
            "transport": "http",
            "url": server_url,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    return connections


def _builtin_authorization_middleware(allowed: frozenset[str], *, has_skills: bool) -> list[object]:
    """Hide ungranted harness tools and reject stale/forged calls defensively.

    Deep Agents registers its harness tools separately from ``tools=``.  A
    model-call middleware is therefore the request-scoped way to trim that
    tool surface without global profile mutation (which would leak privileges
    between concurrent requests).  The tool-call guard remains authoritative
    if an old checkpoint or a malformed request references a hidden tool.
    """

    @wrap_model_call
    async def select_authorized_builtin_tools(
        request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        # A granted Skill is documentation, not a grant of the platform's
        # general file-reading capability.  ``read_file`` is exposed solely so
        # Deep Agents can read the staged /skills/.../SKILL.md instructions.
        visible = allowed | ({"read_file"} if has_skills else set())
        permitted = [
            tool for tool in request.tools
            if getattr(tool, "name", None) not in BUILTIN_TOOL_NAMES or getattr(tool, "name", None) in visible
        ]
        return await handler(request.override(tools=permitted))

    @wrap_tool_call
    async def reject_ungranted_builtin_tool(request, handler):
        name = request.tool_call.get("name", "")
        if name == "read_file" and has_skills:
            file_path = str(request.tool_call.get("args", {}).get("file_path", ""))
            if file_path.startswith(f"{SKILL_VIRTUAL_ROOT}/"):
                return await handler(request)
        if name in BUILTIN_TOOL_NAMES and name not in allowed:
            return ToolMessage(
                content=f"Tool '{name}' is not authorized for the current role.",
                tool_call_id=request.tool_call["id"],
            )
        return await handler(request)

    return [select_authorized_builtin_tools, reject_ungranted_builtin_tool]


async def create_request_agent(
    subject: AuthorizedSubject,
    tools: list[GrantedTool],
    skills: list[GrantedSkill] | None = None,
    checkpointer=None,
    mcp_context: dict[str, str] | None = None,
    system_prompt: str | None = None,
):
    """Build an agent for one request, making cross-request privilege leakage impossible."""
    settings = get_settings()
    if not all((settings.openai_base_url, settings.openai_api_key, settings.openai_model)):
        raise AgentRuntimeError("OPENAI_BASE_URL, OPENAI_API_KEY, and OPENAI_MODEL must be configured")

    # Role grants and API-key file access are both required. The latter is a
    # hard upper bound, so an accidentally broad role cannot give a no-file or
    # read-only key write, delete, or command-execution capability.
    tools = apply_file_access_cap(subject, tools)
    mcp_grants = [tool for tool in tools if tool.source == "mcp"]
    builtin_grants = frozenset(tool.name for tool in tools if tool.source == "builtin")
    mcp_tools = []
    if mcp_grants:
        try:
            mcp_client = MultiServerMCPClient(_connections_for(subject, mcp_grants, mcp_context), tool_name_prefix=False)
            mcp_tools = await mcp_client.get_tools()
        except Exception as exc:
            raise AgentRuntimeError("Unable to load authorized MCP tools") from exc

    model = ChatOpenAI(
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        temperature=0,
        # Do not let provider retries hold a Feishu request for minutes.  A
        # busy upstream should be surfaced promptly so the user can retry.
        timeout=20,
        max_retries=0,
    )
    granted_skill_files = build_skill_files(skills)
    middleware = _builtin_authorization_middleware(builtin_grants, has_skills=bool(granted_skill_files))
    # Planning is opt-in in recent Deep Agents versions.  Register it only
    # when an administrator grants the corresponding built-in capability.
    if "write_todos" in builtin_grants:
        middleware.append(TodoListMiddleware())

    return create_deep_agent(
        model=model,
        tools=mcp_tools,
        # Skill paths are virtual paths populated by ``build_skill_files`` at
        # invocation time.  This keeps the filesystem authoritative while
        # ensuring an agent can only discover its own granted skills.
        skills=[SKILL_VIRTUAL_ROOT] if granted_skill_files else None,
        backend=StateBackend(),
        system_prompt=system_prompt
        or (
            "你是 Weyeah Agents 平台中的 AI 助手。"
            "只可使用本次请求实际提供且已授权的工具与 Skill。"
            "默认使用中文回复，除非用户明确要求其他语言。"
        ),
        # PostgreSQL-backed checkpoints are added in the next persistence milestone.
        checkpointer=checkpointer or False,
        middleware=middleware,
    )
