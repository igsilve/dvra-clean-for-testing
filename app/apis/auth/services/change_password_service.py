from apis.auth.utils import update_user_password, verify_password
from apis.auth.utils.jwt_auth import get_current_user_pending_password_change
from apis.auth.utils.lockout import (
    register_failure,
    register_success,
    seconds_remaining,
)
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from password_policy import validate_password_policy
from pydantic import BaseModel, field_validator
from rate_limiting import limiter
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


class ChangePasswordData(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _enforce_password_policy(cls, value: str) -> str:
        return validate_password_policy(value, subject="new_password")


class ChangePasswordResponse(BaseModel):
    detail: str


@router.post(
    "/profile/password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
def change_password(
    request: Request,
    data: ChangePasswordData,
    # The permissive dependency: an account flagged for a forced change must
    # be able to reach this endpoint and only this endpoint.
    current_user: Annotated[User, Depends(get_current_user_pending_password_change)],
    db: Session = Depends(get_db),
):
    """Let a signed-in account replace its own password.

    This is the recovery path for accounts seeded with a system-generated
    password. The code-by-phone reset flow cannot serve them: it is
    restricted to customers, so staff and the chef would otherwise have no
    way to clear the flag.
    """
    # Throttle state is consulted before the password is verified, so a
    # blocked attempt costs no hash comparison. An attacker holding a stolen
    # token could otherwise guess the current password at will and convert
    # temporary access into permanent account ownership.
    retry_after = seconds_remaining("change-password", current_user.username)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    if not verify_password(data.current_password, current_user.password):
        register_failure("change-password", current_user.username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    register_success("change-password", current_user.username)

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from the current password",
        )

    # Clears must_change_password and bumps the token version, so the token
    # used to make this call stops working along with any other outstanding.
    update_user_password(db, current_user.username, data.new_password)

    return {"detail": "Password updated successfully!"}
