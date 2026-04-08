"""Built-in tools for background callback task lifecycle.

Thin wrappers around the spec-aligned core in dash.mcp.tasks.
Only registered when the app has background callbacks.
"""

from __future__ import annotations

from typing import Any

from mcp.types import (
    CallToolResult,
    CancelTaskRequestParams,
    GetTaskRequestParams,
    TextContent,
    Tool,
)

from dash import get_app
from dash.mcp.tasks import get_task, get_task_result, cancel_task


def _input_schema_from(params_type, description: str) -> dict:
    """Derive a clean tool inputSchema from an MCP request params type."""
    schema = params_type.model_json_schema()
    return {
        "type": "object",
        "properties": {
            "taskId": {
                **schema["properties"]["taskId"],
                "description": description,
            },
        },
        "required": schema["required"],
    }


_TOOL_NAMES = {"get_background_task_result", "cancel_background_task"}

_GET_RESULT_TOOL = Tool(
    name="get_background_task_result",
    description=(
        "Poll for the result of a long-running background callback. "
        "Pass the taskId returned by the original tool call. "
        "If the task is still running, call this tool again. "
        "If complete, returns the callback result."
    ),
    inputSchema=_input_schema_from(
        GetTaskRequestParams,
        "The taskId returned by the background callback tool.",
    ),
)

_CANCEL_TASK_TOOL = Tool(
    name="cancel_background_task",
    description="Cancel a running background callback.",
    inputSchema=_input_schema_from(
        CancelTaskRequestParams,
        "The taskId of the background task to cancel.",
    ),
)


def _has_background_callbacks() -> bool:
    app = get_app()
    return any(
        cb_info.get("background")
        for cb_info in app.callback_map.values()
    )


def get_tool_names() -> set[str]:
    return _TOOL_NAMES if _has_background_callbacks() else set()


def get_tools() -> list[Tool]:
    return [_GET_RESULT_TOOL, _CANCEL_TASK_TOOL] if _has_background_callbacks() else []


def call_tool(tool_name: str, arguments: dict[str, Any], task: dict | None = None) -> CallToolResult:
    task_id = arguments.get("taskId", "")

    if tool_name == "get_background_task_result":
        task_status = get_task(task_id)
        if task_status.status == "completed":
            return get_task_result(task_id)
        return CallToolResult(
            content=[TextContent(type="text", text=task_status.model_dump_json())],
        )

    if tool_name == "cancel_background_task":
        result = cancel_task(task_id)
        return CallToolResult(
            content=[TextContent(type="text", text=result.model_dump_json())],
        )

    raise ValueError(f"Unknown tool: {tool_name}")
