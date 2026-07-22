from fastapi import APIRouter

from backend.modules.messaging.api.routers.messaging_router import router as messaging_router

router = APIRouter()
router.include_router(messaging_router)
