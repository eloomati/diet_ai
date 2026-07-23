from fastapi import APIRouter

from backend.modules.admin.api.routers.dietitian_applications_router import (
    router as dietitian_applications_router,
)
from backend.modules.admin.api.routers.transactions_router import router as transactions_router
from backend.modules.admin.api.routers.users_router import router as users_router

router = APIRouter()
router.include_router(users_router)
router.include_router(dietitian_applications_router)
router.include_router(transactions_router)
