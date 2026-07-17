from fastapi import APIRouter

from backend.modules.nutrition.api.routers.diet_plan_router import router as diet_plan_router
from backend.modules.nutrition.api.routers.profile_router import router as profile_router

router = APIRouter()
router.include_router(profile_router)
router.include_router(diet_plan_router)
