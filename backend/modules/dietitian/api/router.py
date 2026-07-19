from fastapi import APIRouter

from backend.modules.dietitian.api.routers.application_router import router as application_router
from backend.modules.dietitian.api.routers.profile_router import router as profile_router

router = APIRouter()
router.include_router(application_router)
router.include_router(profile_router)
