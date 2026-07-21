from fastapi import APIRouter

from backend.modules.notifications.api.routers.notification_router import (
    router as notification_router,
)

router = APIRouter()
router.include_router(notification_router)
