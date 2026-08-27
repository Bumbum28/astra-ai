from typing import Any

from app.core.unit_of_work import UnitOfWorkFactory
from app.tools.base import BaseTool
from app.tools.contracts import ToolContext, ToolDefinition, ToolExecutionResult


class SearchConversationTool(BaseTool):
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_conversation",
            description="Search recent messages in the active conversation.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string", "minLength": 1}},
                "required": ["query"],
                "additionalProperties": False,
            },
        )

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolExecutionResult:
        if context.conversation_id is None:
            return ToolExecutionResult(
                tool_name=self.definition.name,
                content="No active conversation was supplied.",
            )
        query = str(arguments.get("query") or "").strip().casefold()
        if not query:
            raise ValueError("query is required")
        async with self._uow_factory() as uow:
            conversation = await uow.conversations.get_owned(
                context.conversation_id, context.user_id
            )
            if conversation is None:
                return ToolExecutionResult(
                    tool_name=self.definition.name,
                    content="The conversation is unavailable.",
                )
            messages = await uow.messages.list_context(
                context.conversation_id, limit=200
            )
        matches = [item for item in messages if query in item.content.casefold()]
        content = "\n".join(
            f"{item.role.value}: {item.content}" for item in matches[-20:]
        ) or "No matching conversation messages were found."
        return ToolExecutionResult(
            tool_name=self.definition.name,
            content=content,
            data={"match_count": len(matches)},
        )
