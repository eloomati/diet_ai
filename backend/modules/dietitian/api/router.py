from fastapi import APIRouter

from backend.modules.dietitian.api.routers.application_router import router as application_router

router = APIRouter()
router.include_router(application_router)
