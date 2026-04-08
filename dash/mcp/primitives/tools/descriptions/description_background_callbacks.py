"""Description for background (long-running) callbacks.

Informs the LLM that the tool returns a taskId immediately
and must be polled via get_background_task_result.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dash.mcp.primitives.tools.callback_adapter import CallbackAdapter


def background_callback_description(adapter: CallbackAdapter) -> list[str]:
    """Add async polling instructions for background callbacks."""
    if not adapter._cb_info.get("background"):
        return []

    return [
        "",
        "This is a long-running background operation. "
        "It returns a taskId immediately. "
        "Call tool `get_background_task_result` with the taskId to poll for the result.",
    ]
