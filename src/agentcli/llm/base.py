from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol

from agentcli.types import Message


class LlmClient(Protocol):
    model_name: str
    provider_name: str
    max_context_window: int

    def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        *,
        system_prompt: str,
    ) -> AsyncIterator[dict[str, Any]]: ...
