from fastapi import APIRouter

from app.api.v1.router import router as v1_router
from app.core.config import get_config

config = get_config()
api_router = APIRouter()
api_router.include_router(v1_router, prefix=config.api_v1_prefix)
