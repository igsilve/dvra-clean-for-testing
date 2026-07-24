from apis.auth.utils.text_code_utils import generate_and_send_code_to_user
from db.models import User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from rate_limiting import limiter
from sqlalchemy.orm import Session

router = APIRouter()


class ResetPasswordData(BaseModel):
    username: str


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
def reset_password(
    data: ResetPasswordData,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == data.username).first()
    # Generic response to prevent username enumeration
    if user and user.role == UserRole.CUSTOMER:
        generate_and_send_code_to_user(user, db)
    return {"detail": "If the account exists, a PIN code will be sent to the registered phone number"}
