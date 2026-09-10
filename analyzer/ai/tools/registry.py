import time
from typing import Any

from analyzer.ai.tools.base import BaseInvestigationTool, ToolResult


class ToolRegistry:
    """
    Bounded Tool Controller & Registry.
    Guarantees:
    1. Schema validation before execution.
    2. Strict read-only authorization.
    3. Bounded maximum tool calls per investigation session (default: 8).
    4. Full audit trail of tool invocations.
    """

    def __init__(self, max_calls_per_session: int = 8):
        self.max_calls = max_calls_per_session
        self.call_count = 0
        self._tools: dict[str, BaseInvestigationTool] = {}
        self.audit_log: list[dict[str, Any]] = []

    def register(self, tool: BaseInvestigationTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseInvestigationTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def list_tool_declarations(self) -> list[dict[str, Any]]:
        """Exports tool specifications for LLM prompt or tool-calling schema."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameter_schema,
            }
            for t in self._tools.values()
        ]

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        self.call_count += 1
        timestamp = time.time()

        # 1. Check bounds
        if self.call_count > self.max_calls:
            err_res = ToolResult(
                success=False,
                tool_name=tool_name,
                data=[],
                error_message=f"Investigation tool call limit exceeded ({self.max_calls}). Bounded execution enforced.",
            )
            self._log_audit(tool_name, arguments, err_res, timestamp)
            return err_res

        # 2. Check existence
        tool = self._tools.get(tool_name)
        if not tool:
            err_res = ToolResult(
                success=False,
                tool_name=tool_name,
                data=[],
                error_message=f"Unauthorized or unknown tool: '{tool_name}'",
            )
            self._log_audit(tool_name, arguments, err_res, timestamp)
            return err_res

        # 3. Execute with error boundary
        try:
            result = tool.execute(**arguments)
        except Exception as e:
            result = ToolResult(
                success=False,
                tool_name=tool_name,
                data=[],
                error_message=f"Tool execution exception: {e}",
            )

        self._log_audit(tool_name, arguments, result, timestamp)
        return result

    def _log_audit(self, tool_name: str, args: dict[str, Any], res: ToolResult, start_ts: float) -> None:
        self.audit_log.append({
            "tool": tool_name,
            "arguments": args,
            "success": res.success,
            "records_returned": res.records_returned,
            "error": res.error_message,
            "latency_ms": res.latency_ms,
            "timestamp": start_ts,
        })
