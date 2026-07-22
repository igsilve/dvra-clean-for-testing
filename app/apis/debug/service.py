from apis.debug.services.get_debug_info_service import router as get_debug_info_router
from fastapi import APIRouter

# debug endpoints are excluded from the OpenAPI schema
router = APIRouter(include_in_schema=False)
router.include_router(get_debug_info_router)
