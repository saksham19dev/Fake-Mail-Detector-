from fastapi import APIRouter
from backend.app.api.v1.analyze import router as analyze_router
from backend.app.api.v1.reports import router as reports_router

router = APIRouter()
router.include_router(analyze_router)
router.include_router(reports_router)
