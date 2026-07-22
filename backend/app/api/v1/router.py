from fastapi import APIRouter

from app.domains.auth.router import router as auth_router
from app.domains.chat.router import router as chat_router
from app.domains.conversations.router import router as conversations_router
from app.domains.health.router import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(conversations_router)
router.include_router(chat_router)
