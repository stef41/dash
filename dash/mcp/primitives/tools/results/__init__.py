"""Tool result formatting for MCP tools/call responses.

Each result formatter shares the same signature:
``(output: MCPOutput, value: Any) -> list[TextContent | ImageContent]``

Formatters decide for themselves whether they care about a given output.
The structuredContent is always the full dispatch response.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.types import CallToolResult, CreateTaskResult, TextContent

from dash.types import CallbackDispatchResponse
from dash.mcp.primitives.tools.callback_adapter import CallbackAdapter

from .result_dataframe import dataframe_result
from .result_plotly_figure import plotly_figure_result

_RESULT_FORMATTERS = [
    plotly_figure_result,
    dataframe_result,
]


def format_callback_response(
    response: CallbackDispatchResponse,
    callback: CallbackAdapter,
) -> CallToolResult:
    """Format a dispatch response as a CallToolResult.

    The response is always returned as structuredContent. Result
    formatters are called per output property and may add additional
    content items (images, markdown, etc.).
    """
    content: list[Any] = [
        TextContent(type="text", text=json.dumps(response, default=str)),
    ]

    resp = response.get("response") or {}
    for callback_output in callback.outputs:
        value = resp.get(callback_output["component_id"], {}).get(callback_output["property"])
        for result_fn in _RESULT_FORMATTERS:
            content.extend(result_fn(callback_output, value))

    return CallToolResult(
        content=content,
        structuredContent=response,
    )


def task_result_to_tool_result(create_task_result: CreateTaskResult) -> CallToolResult:
    """Wrap a CreateTaskResult as a CallToolResult with polling instructions.

    MCP Tasks are not yet supported by LLM clients, so this converts the
    task metadata into a tool response that guides the LLM to poll via
    the get_background_task_result tool.
    """
    task = create_task_result.task
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=json.dumps({
                "taskId": task.taskId,
                "status": task.status,
                "pollInterval": task.pollInterval,
                "message": (
                    "This is a long-running background callback. "
                    "Call the get_background_task_result tool with this taskId "
                    "to poll for the result."
                ),
            }),
        )],
    )
