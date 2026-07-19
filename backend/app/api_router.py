from fastapi import APIRouter

from backend.modules.admin.api.router import router as admin_router
from backend.modules.conversation.api.router import router as conversation_router
from backend.modules.dietitian.api.router import router as dietitian_router
from backend.modules.identity.api.router import router as identity_router
from backend.modules.nutrition.api.router import router as nutrition_router
from backend.modules.transactions.api.router import router as transactions_router

api_router = APIRouter()
api_router.include_router(identity_router)
api_router.include_router(conversation_router)
api_router.include_router(nutrition_router)
api_router.include_router(dietitian_router)
api_router.include_router(admin_router)
api_router.include_router(transactions_router)