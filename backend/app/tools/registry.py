from collections.abc import Callable, Iterable

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import AppException
from app.tools.base import BaseTool
from app.tools.contracts import ToolDefinition

ToolFactory = Callable[[], BaseTool]


class ToolRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ToolFactory] = {}

    def register(self, name: str, factory: ToolFactory) -> None:
        if name in self._factories:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._factories[name] = factory

    def resolve(self, name: str) -> BaseTool:
        factory = self._factories.get(name)
        if factory is None:
            raise AppException(
                ErrorCode.TOOL_NOT_FOUND,
                f"Tool '{name}' is not registered.",
                status_code=404,
            )
        return factory()

    def definitions(self) -> list[ToolDefinition]:
        return [factory().definition for factory in self._factories.values()]

    def names(self) -> Iterable[str]:
        return self._factories.keys()
