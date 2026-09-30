import secrets
from datetime import datetime

from apis.auth.schemas import NewPasswordData
from apis.auth.utils import update_user_password
from apis.auth.utils.lockout import (
    register_failure,
    register_success,
    seconds_remaining,
)
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from rate_limiting import limiter
from sqlalchemy.orm import Session

ACCESS_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 1 week

router = APIRouter()


@router.post(
    "/reset-password/new-password",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
def set_new_password(
    request: Request,
    data: NewPasswordData,
    db: Session = Depends(get_db),
):
    # A single generic error keeps the endpoint from disclosing whether the
    # username exists or which stage of the reset flow failed.
    invalid = HTTPException(
        status_code=400,
        detail="Invalid username or reset password code",
    )

    retry_after = seconds_remaining("reset-code", data.username)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = db.query(User).filter(User.username == data.username).first()
    if not user or not user.reset_password_code:
        register_failure("reset-code", data.username)
        raise invalid

    if (
        not user.reset_password_code_expiry_date
        or datetime.now() > user.reset_password_code_expiry_date
    ):
        register_failure("reset-code", data.username)
        raise invalid

    if not secrets.compare_digest(user.reset_password_code, data.reset_password_code):
        register_failure("reset-code", data.username)
        raise invalid

    update_user_password(db, user.username, data.new_password)
    user.reset_password_code = None
    user.reset_password_code_expiry_date = None
    db.add(user)
    db.commit()
    register_success("reset-code", data.username)

    return {"detail": "Password updated successfully!"}
