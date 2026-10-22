from __future__ import annotations

import asyncio
from typing import Any

from agentcli.policy import AuditLog
from agentcli.tools.base import Tool, ToolContext, ToolDecision, ToolResult
from agentcli.tools.registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def execute_all(
        self,
        calls: list[dict[str, Any]],
        context: ToolContext,
    ) -> list[ToolResult]:
        read_calls: list[tuple[dict[str, Any], Tool]] = []
        sequential_calls: list[tuple[dict[str, Any], Tool | None]] = []

        for call in calls:
            name = _tool_call_name(call)
            tool = self.registry.get(name)
            if tool and tool.is_read_only and tool.is_concurrency_safe:
                read_calls.append((call, tool))
            else:
                sequential_calls.append((call, tool))

        results: list[ToolResult] = []
        if read_calls:
            semaphore = asyncio.Semaphore(context.config.tools.max_concurrent_read)

            async def run_read(call: dict[str, Any], tool: Tool) -> ToolResult:
                async with semaphore:
                    return await self._execute_single(call, tool, context)

            results.extend(
                await asyncio.gather(*(run_read(call, tool) for call, tool in read_calls))
            )

        for call, tool in sequential_calls:
            results.append(await self._execute_single(call, tool, context))

        return results

    async def _execute_single(
        self,
        call: dict[str, Any],
        tool: Tool | None,
        context: ToolContext,
    ) -> ToolResult:
        tool_call_id = str(call.get("id") or "")
        name = _tool_call_name(call)
        payload = _tool_call_arguments(call)

        if not tool:
            return ToolResult(
                tool_use_id=tool_call_id,
                content=(
                    f'Tool "{name}" not found. Available tools: '
                    f"{', '.join(self.registry.list_names())}"
                ),
                is_error=True,
            )

        audit = AuditLog(context.config.policy.audit_log_path)
        approver = "none"
        try:
            data = tool.validate(payload)
            decision = await self._approval_decision(tool, data, context)
            if decision in {"deny", "skip"}:
                approver = "hitl"
                audit.record(
                    tool_name=tool.name,
                    input_data=data,
                    outcome=decision,
                    approver=approver,
                    cwd=context.cwd,
                )
                return ToolResult(
                    tool_use_id=tool_call_id,
                    content=(
                        f'Tool "{tool.name}" was '
                        f"{'denied' if decision == 'deny' else 'skipped'} by approval policy."
                    ),
                    is_error=True,
                )
            if tool.requires_approval or context.config.policy.hitl_mode == "always":
                approver = "hitl"

            result = await tool.execute(data, context)
            result.tool_use_id = tool_call_id
            if not tool.is_read_only and context.config.features.audit_log:
                audit.record(
                    tool_name=tool.name,
                    input_data=data,
                    outcome="allow" if not result.is_error else "error",
                    approver=approver,
                    cwd=context.cwd,
                )
            return result
        except Exception as exc:  # noqa: BLE001 - tool errors must flow back to the model
            if context.config.features.audit_log and tool and not tool.is_read_only:
                audit.record(
                    tool_name=tool.name,
                    input_data=payload,
                    outcome="error",
                    approver=approver,
                    cwd=context.cwd,
                )
            return ToolResult(
                tool_use_id=tool_call_id,
                content=f'Tool "{name}" execution error: {exc}',
                is_error=True,
            )

    async def _approval_decision(
        self,
        tool: Tool,
        payload: dict[str, Any],
        context: ToolContext,
    ) -> ToolDecision:
        mode = context.config.policy.hitl_mode
        if mode == "never":
            return "approve"
        if mode == "auto" and not tool.requires_approval:
            return "approve"
        if not context.approval_callback:
            return "deny"
        result = context.approval_callback(
            {
                "tool_name": tool.name,
                "input": payload,
                "danger_level": tool.danger_level,
                "description": tool.description,
            }
        )
        if asyncio.iscoroutine(result):
            result = await result
        return result


def _tool_call_name(call: dict[str, Any]) -> str:
    function = call.get("function") if isinstance(call.get("function"), dict) else {}
    return str(function.get("name") or call.get("name") or "")


def _tool_call_arguments(call: dict[str, Any]) -> dict[str, Any]:
    function = call.get("function") if isinstance(call.get("function"), dict) else {}
    arguments = function.get("arguments", call.get("arguments", {}))
    if isinstance(arguments, str):
        import json

        try:
            parsed = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            parsed = {"raw": arguments}
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    return arguments if isinstance(arguments, dict) else {}
