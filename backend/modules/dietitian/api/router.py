from fastapi import APIRouter

from backend.modules.dietitian.api.routers.application_router import router as application_router
from backend.modules.dietitian.api.routers.marketplace_router import router as marketplace_router
from backend.modules.dietitian.api.routers.profile_router import router as profile_router
from backend.modules.dietitian.api.routers.review_router import router as review_router

router = APIRouter()
router.include_router(application_router)
router.include_router(profile_router)
# Registered last — its `/{dietitian_id}` catches any single extra path
# segment under `/dietitian`, so the literal-path routers above must be
# tried first (no real collision exists today, but registration order is
# what would matter if one ever did).
router.include_router(review_router)
router.include_router(marketplace_router)
