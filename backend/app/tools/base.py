from abc import ABC, abstractmethod
from typing import Any

from app.tools.contracts import ToolContext, ToolDefinition, ToolExecutionResult


class BaseTool(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Describe the tool using provider-independent JSON Schema."""

    @abstractmethod
    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolExecutionResult:
        """Execute a validated tool request in an authorization context."""
