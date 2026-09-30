import secrets
import string

from apis.auth.utils import RolesBasedAuthChecker, update_user_password
from config import settings
from db.models import UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.post(
    "/admin/reset-chef-password",
    include_in_schema=False,
    status_code=status.HTTP_200_OK,
)
def reset_chef_password(
    _: Annotated[bool, Depends(RolesBasedAuthChecker([UserRole.CHEF]))],
    db: Session = Depends(get_db),
):
    # Authorization is a role decision made server-side. The source address
    # (request.client.host / X-Forwarded-For) is attacker-influenceable behind
    # a proxy and is never used to grant access.
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_-+=;:[]"

    new_password = "".join(secrets.choice(characters) for _ in range(32))
    update_user_password(db, settings.CHEF_USERNAME, new_password)

    return {"password": new_password}
