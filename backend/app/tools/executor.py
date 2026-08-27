import asyncio
from typing import Any

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import AppException, AuthorizationException
from app.tools.contracts import ToolContext, ToolExecutionResult
from app.tools.registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, *, timeout_seconds: float) -> None:
        self._registry = registry
        self._timeout_seconds = timeout_seconds

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolExecutionResult:
        """Resolve, authorize and execute one tool with a hard timeout."""
        if context.allowed_tools is not None and tool_name not in context.allowed_tools:
            raise AuthorizationException(
                f"Tool '{tool_name}' is not allowed for this execution.",
                code=ErrorCode.TOOL_FORBIDDEN,
            )
        tool = self._registry.resolve(tool_name)
        try:
            async with asyncio.timeout(self._timeout_seconds):
                return await tool.execute(arguments, context)
        except TimeoutError as exc:
            raise AppException(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Tool '{tool_name}' timed out.",
                status_code=504,
            ) from exc
        except AppException:
            raise
        except Exception as exc:
            raise AppException(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Tool '{tool_name}' failed.",
                status_code=502,
                details={"exception": type(exc).__name__},
            ) from exc
