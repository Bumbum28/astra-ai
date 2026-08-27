from fastapi import APIRouter

from app.agents.router import router as agents_router
from app.domains.auth.router import router as auth_router
from app.domains.characters.router import router as characters_router
from app.domains.chat.router import router as chat_router
from app.domains.conversations.router import router as conversations_router
from app.domains.health.router import router as health_router
from app.domains.knowledge.router import router as knowledge_router
from app.domains.memories.router import router as memories_router
from app.domains.personas.router import router as personas_router
from app.tools.router import router as tools_router

router = APIRouter()
router.include_router(agents_router)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(characters_router)
router.include_router(personas_router)
router.include_router(memories_router)
router.include_router(knowledge_router)
router.include_router(tools_router)
router.include_router(conversations_router)
router.include_router(chat_router)
