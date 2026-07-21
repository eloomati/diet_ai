from fastapi import APIRouter

from backend.modules.transactions.api.routers.transaction_router import router as transaction_router

router = APIRouter()
router.include_router(transaction_router)
