from dataclasses import dataclass

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import AppException
from app.tools.registry import ToolRegistry


@dataclass(frozen=True, slots=True)
class AgentPolicy:
    max_steps: int
    max_tool_calls: int
    timeout_seconds: float
    default_allowed_tools: frozenset[str]

    def resolve_allowed_tools(
        self,
        registry: ToolRegistry,
        requested: list[str] | None,
    ) -> frozenset[str]:
        """Return an explicit allow-list and reject unknown tool names."""
        registered = set(registry.names())
        configured = set(self.default_allowed_tools)
        unavailable = configured - registered
        if unavailable:
            raise AppException(
                ErrorCode.AGENT_INVALID_TOOL,
                "Configured agent tool is not registered.",
                status_code=500,
                details={"tools": sorted(unavailable)},
            )

        desired = set(requested) if requested is not None else configured
        unknown = desired - registered
        forbidden = desired - configured
        if unknown or forbidden:
            raise AppException(
                ErrorCode.AGENT_INVALID_TOOL,
                "Requested agent tool is not allowed.",
                status_code=422,
                details={"tools": sorted(unknown | forbidden)},
            )
        return frozenset(desired)
