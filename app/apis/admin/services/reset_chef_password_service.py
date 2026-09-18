import secrets
import string

from apis.auth.utils import get_current_user
from apis.auth.utils import update_user_password
from config import settings
from db.models import User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.post(
    "/admin/reset-chef-password",
    include_in_schema=False,
    status_code=status.HTTP_200_OK,
)
def get_reset_chef_password(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    client_host = request.client.host

    if current_user.role != UserRole.CHEF.value:
        raise HTTPException(
            status_code=403,
            detail="Only Chef is authorized to reset the Chef password!",
        )

    if client_host not in ("127.0.0.1", "::1"):
        raise HTTPException(
            status_code=403,
            detail="Chef password can be reseted only from the local machine!",
        )

    characters = string.ascii_letters + string.digits + "!@#$%^&*()_-+=;:[]"

    new_password = "".join(secrets.choice(characters) for i in range(32))
    update_user_password(db, settings.CHEF_USERNAME, new_password)

    return {"detail": "Chef password was reset successfully"}
