"""Feishu long-connection worker for Deep Agents."""

from __future__ import annotations

import json
import logging
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import lark_oapi as lark
from dotenv import load_dotenv
from lark_oapi.api.im.v1 import (
    CreateMessageReactionRequest,
    CreateMessageReactionRequestBody,
    CreateMessageRequest,
    CreateMessageRequestBody,
    DeleteMessageReactionRequest,
    Emoji,
    P2ImMessageReceiveV1,
)
from lark_oapi.api.contact.v3 import GetUserRequest

SERVICE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(SERVICE_DIR / ".env")
LOGGER = logging.getLogger("deep_agents.feishu")
EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="feishu-agent")
TEXT_MESSAGE_TYPE = "text"
TYPING_EMOJI = "Typing"
MAX_REPLY_CHARS = 3_500
HELP_TEXT = (
    "可用指令：\n"
    "/new 项目A讨论：新建并切换会话\n"
    "/sessions 页数：查看当前聊天中的会话（页数可省略）\n"
    "/switch 编号：切换会话\n"
    "/del 编号：删除非当前会话"
)


class ConfigurationError(RuntimeError):
    pass


class RecentMessageIds:
    def __init__(self, limit: int = 2_000) -> None:
        self.values: set[str] = set()
        self.queue: deque[str] = deque()
        self.limit = limit
        self.lock = threading.Lock()

    def seen_or_add(self, message_id: str) -> bool:
        with self.lock:
            if message_id in self.values:
                return True
            self.values.add(message_id)
            self.queue.append(message_id)
            if len(self.queue) > self.limit:
                self.values.remove(self.queue.popleft())
            return False


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("YOUR_") or value.startswith("cli_your_"):
        raise ConfigurationError(f"{name} must be configured in {SERVICE_DIR / '.env'}")
    return value


def _extract_text(content: str) -> str:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return ""
    return str(parsed.get("text", "")).strip() if isinstance(parsed, dict) else ""


def _scope(data: P2ImMessageReceiveV1) -> dict[str, str]:
    sender_id = data.event.sender.sender_id
    open_id = getattr(sender_id, "open_id", None) or getattr(sender_id, "user_id", None) or ""
    tenant_key = getattr(data.event.sender, "tenant_key", None) or getattr(data, "tenant_key", None) or ""
    return {"tenant_key": tenant_key or "default", "open_id": open_id, "chat_id": data.event.message.chat_id, "chat_type": getattr(data.event.message, "chat_type", "unknown")}


class InternalApiClient:
    """Calls FastAPI only; the Worker never opens a database connection."""

    def __init__(self, api_base_url: str, platform_api_key: str, internal_secret: str) -> None:
        self.chat_url = f"{api_base_url.rstrip('/')}/chat/completions"
        self.internal_url = api_base_url.rstrip("/").removesuffix("/v1") + "/internal/feishu"
        self.platform_api_key = platform_api_key
        self.internal_secret = internal_secret

    def _request(self, url: str, *, method: str = "GET", payload: dict | None = None) -> object:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={"Content-Type": "application/json; charset=utf-8", "X-Feishu-Internal-Secret": self.internal_secret},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))

    def resolve_session(self, scope: dict[str, str]) -> dict:
        return self._request(f"{self.internal_url}/sessions/resolve", method="POST", payload=scope)  # type: ignore[return-value]

    def upsert_user(self, scope: dict[str, str], display_name: str, avatar_url: str | None) -> None:
        self._request(f"{self.internal_url}/users/upsert", method="POST", payload={"tenant_key": scope["tenant_key"], "open_id": scope["open_id"], "display_name": display_name, "avatar_url": avatar_url})

    def new_session(self, scope: dict[str, str], title: str) -> dict:
        return self._request(f"{self.internal_url}/sessions/new", method="POST", payload={**scope, "title": title})  # type: ignore[return-value]

    def list_sessions(self, scope: dict[str, str], page: int) -> list[dict]:
        query = urllib.parse.urlencode({**scope, "page": page})
        return self._request(f"{self.internal_url}/sessions?{query}")  # type: ignore[return-value]

    def switch_session(self, scope: dict[str, str], ordinal: int) -> dict:
        return self._request(f"{self.internal_url}/sessions/switch", method="POST", payload={**scope, "ordinal": ordinal})  # type: ignore[return-value]

    def archive_session(self, scope: dict[str, str], ordinal: int) -> None:
        self._request(f"{self.internal_url}/sessions/archive", method="POST", payload={**scope, "ordinal": ordinal})

    def ask(self, text: str, thread_id: str, scope: dict[str, str]) -> str:
        payload = {"model": "deep-agents-feishu", "messages": [{"role": "user", "content": text}], "stream": False}
        request = urllib.request.Request(
            self.chat_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.platform_api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "X-DeepAgents-Thread-Id": thread_id,
                "X-Feishu-Internal-Secret": self.internal_secret,
                "X-Feishu-Tenant-Key": scope["tenant_key"],
                "X-Feishu-Open-Id": scope["open_id"],
                "X-Feishu-Chat-Type": scope.get("chat_type", "unknown"),
            },
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
        return str(result["choices"][0]["message"]["content"]).strip() or "暂时没有生成回复。"


class FeishuBot:
    def __init__(self) -> None:
        self.app_id = _required("FEISHU_APP_ID")
        self.app_secret = _required("FEISHU_APP_SECRET")
        self.api = InternalApiClient(
            _required("FEISHU_AGENT_API_BASE_URL"), _required("FEISHU_PLATFORM_API_KEY"), _required("FEISHU_INTERNAL_AUTH_SECRET")
        )
        self.client = lark.Client.builder().app_id(self.app_id).app_secret(self.app_secret).build()
        self.recent_messages = RecentMessageIds()

    def reply(self, chat_id: str, text: str) -> None:
        for start in range(0, max(len(text), 1), MAX_REPLY_CHARS):
            chunk = text[start : start + MAX_REPLY_CHARS] or "暂时没有生成回复。"
            request = CreateMessageRequest.builder().receive_id_type("chat_id").request_body(
                CreateMessageRequestBody.builder().receive_id(chat_id).msg_type(TEXT_MESSAGE_TYPE).content(json.dumps({"text": chunk}, ensure_ascii=False)).build()
            ).build()
            response = self.client.im.v1.message.create(request)
            if not response.success():
                LOGGER.error("Unable to send Feishu reply: code=%s msg=%s", response.code, response.msg)

    def add_typing_reaction(self, message_id: str) -> str | None:
        request = CreateMessageReactionRequest.builder().message_id(message_id).request_body(
            CreateMessageReactionRequestBody.builder().reaction_type(Emoji.builder().emoji_type(TYPING_EMOJI).build()).build()
        ).build()
        response = self.client.im.v1.message_reaction.create(request)
        if response.success() and response.data:
            return response.data.reaction_id
        LOGGER.warning("Unable to add typing reaction: code=%s msg=%s", response.code, response.msg)
        return None

    def profile(self, open_id: str) -> tuple[str, str | None]:
        try:
            response = self.client.contact.v3.user.get(
                GetUserRequest.builder().user_id_type("open_id").user_id(open_id).build()
            )
            user = response.data.user if response.success() and response.data else None
            avatar = getattr(user, "avatar", None)
            return (getattr(user, "name", None) or open_id, getattr(avatar, "avatar_72", None))
        except Exception:
            LOGGER.warning("Unable to load Feishu user profile: %s", open_id)
            return open_id, None

    def remove_reaction(self, message_id: str, reaction_id: str | None) -> None:
        if not reaction_id:
            return
        response = self.client.im.v1.message_reaction.delete(
            DeleteMessageReactionRequest.builder().message_id(message_id).reaction_id(reaction_id).build()
        )
        if not response.success():
            LOGGER.warning("Unable to remove typing reaction: code=%s msg=%s", response.code, response.msg)

    def _command_reply(self, text: str, scope: dict[str, str]) -> str | None:
        command, _, argument = text.partition(" ")
        argument = argument.strip()
        if command == "/new":
            if not argument:
                return "用法：/new 会话名称"
            record = self.api.new_session(scope, argument)
            return f"已新建并切换到会话 #{record['ordinal']}：{record['title']}"
        if command == "/sessions":
            if argument and (not argument.isdigit() or int(argument) < 1):
                return "用法：/sessions [页数]"
            page = int(argument or 1)
            records = self.api.list_sessions(scope, page)
            if not records:
                return f"第 {page} 页没有可见会话。"
            lines = [f"会话列表（第 {page} 页）："]
            for record in records:
                marker = " ← 当前" if record["is_current"] else ""
                lines.append(f"#{record['ordinal']}  {record['title']}{marker}")
            return "\n".join(lines)
        if command == "/switch":
            if not argument.isdigit() or int(argument) < 1:
                return "用法：/switch 编号"
            record = self.api.switch_session(scope, int(argument))
            return f"已切换到会话 #{record['ordinal']}：{record['title']}"
        if command == "/del":
            if not argument.isdigit() or int(argument) < 1:
                return "用法：/del 编号"
            self.api.archive_session(scope, int(argument))
            return f"已删除会话 #{argument}。"
        return HELP_TEXT

    def _process_message(self, chat_id: str, message_id: str, text: str, scope: dict[str, str]) -> None:
        try:
            display_name, avatar_url = self.profile(scope["open_id"])
            self.api.upsert_user(scope, display_name, avatar_url)
            if text.startswith("/"):
                self.reply(chat_id, self._command_reply(text, scope) or HELP_TEXT)
                return
            reaction_id = self.add_typing_reaction(message_id)
            try:
                current = self.api.resolve_session(scope)
                answer = self.api.ask(text, current["thread_id"], scope)
                self.reply(chat_id, answer)
            finally:
                self.remove_reaction(message_id, reaction_id)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            LOGGER.warning("API rejected message: status=%s detail=%s", exc.code, detail[:300])
            if exc.code == 409 and "current session" in detail:
                self.reply(chat_id, "不能删除当前会话，请先使用 /switch 切换到其他会话。")
            elif exc.code == 404:
                self.reply(chat_id, "会话编号不存在，请使用 /sessions 查看会话列表。")
            elif exc.code == 429:
                self.reply(chat_id, "模型服务当前限流或额度已耗尽，请稍后再试。")
            elif exc.code == 503:
                self.reply(chat_id, "模型服务当前繁忙，请稍后重试。")
            else:
                self.reply(chat_id, "请求未能完成，请稍后再试。")
        except Exception:
            LOGGER.exception("Unhandled Feishu message processing error: message_id=%s", message_id)
            self.reply(chat_id, "抱歉，处理消息时发生错误，请稍后再试。")

    def handle_message(self, data: P2ImMessageReceiveV1) -> None:
        event = data.event
        if event.message.message_type != TEXT_MESSAGE_TYPE:
            return
        message_id = event.message.message_id
        if self.recent_messages.seen_or_add(message_id):
            return
        text = _extract_text(event.message.content)
        if not text:
            self.reply(event.message.chat_id, "目前只支持文本消息。")
            return
        EXECUTOR.submit(self._process_message, event.message.chat_id, message_id, text, _scope(data))

    def run(self) -> None:
        handler = lark.EventDispatcherHandler.builder("", "").register_p2_im_message_receive_v1(self.handle_message).build()
        LOGGER.info("Starting Feishu long-connection worker")
        lark.ws.Client(self.app_id, self.app_secret, event_handler=handler).start()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        FeishuBot().run()
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc


if __name__ == "__main__":
    main()
