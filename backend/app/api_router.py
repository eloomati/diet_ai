from fastapi import APIRouter

from backend.modules.conversation.api.router import router as conversation_router
from backend.modules.identity.api.router import router as identity_router
from backend.modules.nutrition.api.router import router as nutrition_router

api_router = APIRouter()
api_router.include_router(identity_router)
api_router.include_router(conversation_router)
api_router.include_router(nutrition_router)