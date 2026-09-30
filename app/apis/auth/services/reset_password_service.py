from apis.auth.utils import may_use_self_service_password_reset
from apis.auth.utils.text_code_utils import generate_and_send_code_to_user
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from rate_limiting import limiter
from sqlalchemy.orm import Session

router = APIRouter()


class ResetPasswordData(BaseModel):
    username: str


class ResetPasswordResponse(BaseModel):
    detail: str


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/minute")
def reset_password(
    request: Request,
    data: ResetPasswordData,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid username",
        )
    # The role rule lives in the authorization module, not inline here, so
    # there is one place to look when the policy changes.
    if not may_use_self_service_password_reset(user):
        raise HTTPException(
            status_code=400,
            detail="Only customers can reset their password through this feature",
        )

    generate_and_send_code_to_user(user, db)
    return {"detail": "PIN code sent to your phone number"}
