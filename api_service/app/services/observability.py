"""Optional Langfuse tracing for request-scoped agent execution."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

LOGGER = logging.getLogger(__name__)


def _enabled() -> bool:
    return all(os.getenv(name, "").strip() for name in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL"))


def langfuse_callbacks() -> list[Any]:
    """Return the LangChain callback only when Langfuse is configured."""
    if not _enabled():
        return []
    try:
        from langfuse.langchain import CallbackHandler

        return [CallbackHandler()]
    except Exception:
        LOGGER.exception("Unable to initialize Langfuse LangChain callback; continuing without tracing")
        return []


@contextmanager
def observe_chat_request(*, user_id: str, session_id: str, model: str, source: str, messages: list[dict[str, str]]) -> Iterator[Any | None]:
    """Create a root trace while keeping observability failures out of user traffic."""
    if not _enabled():
        yield None
        return
    try:
        from langfuse import get_client, propagate_attributes

        client = get_client()
        observation = client.start_as_current_observation(as_type="agent", name="chat-completion")
    except Exception:
        LOGGER.exception("Unable to start Langfuse trace; continuing without tracing")
        yield None
        return

    with observation:
        with propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            tags=["deep-agents", source],
            metadata={"model": model, "source": source},
        ):
            try:
                observation.update(input={"messages": messages})
            except Exception:
                LOGGER.warning("Unable to attach Langfuse trace input", exc_info=True)
            yield observation


def record_chat_output(observation: Any | None, content: str) -> None:
    if observation is None:
        return
    try:
        observation.update(output={"content": content})
    except Exception:
        LOGGER.warning("Unable to attach Langfuse trace output", exc_info=True)
