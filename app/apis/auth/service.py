from apis.auth.services.get_profile_service import router as get_profile_router
from apis.auth.services.get_token_service import router as get_token_router
from apis.auth.services.logout_service import router as logout_router
from apis.auth.services.patch_profile_service import router as patch_profile_router
from apis.auth.services.register_user_service import router as register_user_router
from apis.auth.services.reset_password_new_password_service import (
    router as reset_password_new_password_router,
)
from apis.auth.services.reset_password_service import router as reset_password_router
from apis.auth.services.restrict_processing_service import (
    router as restrict_processing_router,
)
from apis.auth.services.sso_service import router as sso_router
from apis.auth.services.update_profile_service import router as update_profile_router
from apis.auth.services.withdraw_consent_service import router as withdraw_consent_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(get_profile_router)
router.include_router(get_token_router)
router.include_router(register_user_router)
router.include_router(update_profile_router)
router.include_router(patch_profile_router)
router.include_router(reset_password_router)
router.include_router(reset_password_new_password_router)
router.include_router(sso_router)
router.include_router(restrict_processing_router)
router.include_router(withdraw_consent_router)
router.include_router(logout_router)
