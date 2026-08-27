from typing import Any

from app.rag.contracts import RetrievalQuery
from app.rag.service import RAGService
from app.tools.base import BaseTool
from app.tools.contracts import ToolContext, ToolDefinition, ToolExecutionResult


class SearchKnowledgeTool(BaseTool):
    def __init__(self, rag_service: RAGService, *, default_top_k: int = 5) -> None:
        self._rag_service = rag_service
        self._default_top_k = default_top_k

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_knowledge",
            description="Search the current user's Astra knowledge base for relevant passages.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        )

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolExecutionResult:
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")
        raw_top_k = arguments.get("top_k", self._default_top_k)
        top_k = min(max(int(raw_top_k), 1), 20)
        hits = await self._rag_service.search(
            RetrievalQuery(user_id=context.user_id, query=query, top_k=top_k)
        )
        content = "\n\n".join(
            f"[{index}] {hit.content}" for index, hit in enumerate(hits, start=1)
        ) or "No matching knowledge was found."
        return ToolExecutionResult(
            tool_name=self.definition.name,
            content=content,
            data={"hits": [hit.model_dump(mode="json") for hit in hits]},
        )
