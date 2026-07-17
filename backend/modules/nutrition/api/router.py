from fastapi import APIRouter

from backend.modules.nutrition.api.routers.profile_router import router as profile_router

router = APIRouter()
router.include_router(profile_router)
