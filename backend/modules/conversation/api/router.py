from fastapi import APIRouter

from backend.modules.conversation.api.routers.conversation_router import router as conversation_router

router = APIRouter()
router.include_router(conversation_router)
