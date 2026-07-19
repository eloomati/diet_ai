from fastapi import APIRouter

from backend.modules.identity.api.routers.admin_router import router as admin_router
from backend.modules.identity.api.routers.auth_router import router as auth_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(admin_router)