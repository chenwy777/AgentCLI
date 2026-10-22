from __future__ import annotations

import asyncio

import httpx
import pytest

from agentcli.config import load_config
from agentcli.tools import ToolRegistry, get_builtin_tools
from agentcli.tools.base import ToolContext
from agentcli.tools.executor import ToolExecutor
from agentcli.web.fetch import NetworkPolicyError, fetch_url


def test_read_write_file_tool(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    config = load_config(project_root=tmp_path)
    config.policy.hitl_mode = "never"
    registry = ToolRegistry()
    registry.register_all(get_builtin_tools())
    context = ToolContext(cwd=str(tmp_path), config=config)

    async def run():
        write = registry.get("write_file")
        read = registry.get("read_file")
        assert write and read
        write_result = await write.execute(
            {"path": "hello.txt", "content": "hello\nworld\n"},
            context,
        )
        read_result = await read.execute({"path": "hello.txt"}, context)
        return write_result, read_result

    write_result, read_result = asyncio.run(run())
    assert not write_result.is_error
    assert "1: hello" in read_result.content
    assert "2: world" in read_result.content


def test_web_fetch_rejects_redirect_to_local_address(monkeypatch):
    requests: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url)
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"})

    transport = httpx.MockTransport(handler)
    original_client = httpx.AsyncClient

    def test_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", test_client)

    with pytest.raises(NetworkPolicyError, match="private or local"):
        asyncio.run(fetch_url("http://93.184.216.34/start"))

    assert len(requests) == 1


def test_tool_executor_reports_denied_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    config = load_config(project_root=tmp_path)
    registry = ToolRegistry()
    registry.register_all(get_builtin_tools())

    def deny(_payload):
        return "deny"

    context = ToolContext(cwd=str(tmp_path), config=config, approval_callback=deny)
    calls = [
        {
            "id": "blocked",
            "function": {"name": "bash", "arguments": '{"command":"echo no"}'},
        }
    ]

    result = asyncio.run(ToolExecutor(registry).execute_all(calls, context))

    assert result[0].is_error
    assert result[0].content == 'Tool "bash" was denied by approval policy.'
