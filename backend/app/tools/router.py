from typing import Annotated

from fastapi import APIRouter, Depends

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.users.schemas import UserResponse
from app.tools.contracts import ToolDefinition
from app.tools.dependencies import get_tool_registry
from app.tools.registry import ToolRegistry

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=ApiResponse[list[ToolDefinition]])
async def list_tools(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    registry: Annotated[ToolRegistry, Depends(get_tool_registry)],
) -> ApiResponse[list[ToolDefinition]]:
    _ = current_user
    return ApiResponse[list[ToolDefinition]].ok(registry.definitions())
