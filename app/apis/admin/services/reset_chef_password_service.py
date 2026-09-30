import secrets
import string

from apis.auth.utils import (
    Permission,
    Requires,
    update_user_password,
    verify_password,
)
from apis.auth.utils.lockout import (
    register_failure,
    register_success,
    seconds_remaining,
)
from audit_log import audit
from config import settings
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from password_policy import PasswordPolicyError, validate_password_policy
from pydantic import BaseModel, ConfigDict
from rate_limiting import limiter
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


class ChefPasswordResponse(BaseModel):
    password: str


class ChefPasswordResetRequest(BaseModel):
    """Step-up re-authentication for the highest-value operation here.

    Rotating the privileged account's password is account takeover if a
    token is replayed, and a token is the one thing an attacker is most
    likely to have. Proving possession of the current password costs a
    legitimate operator one field and costs a token thief the whole
    operation.
    """

    model_config = ConfigDict(extra="forbid")

    current_password: str


@router.post(
    "/admin/reset-chef-password",
    response_model=ChefPasswordResponse,
    include_in_schema=False,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/minute")
def reset_chef_password(
    request: Request,
    credentials: ChefPasswordResetRequest,
    current_user: Annotated[User, Depends(Requires(Permission.RESET_CHEF_PASSWORD))],
    db: Session = Depends(get_db),
):
    # Authorization is a role decision made server-side. The source address
    # (request.client.host / X-Forwarded-For) is attacker-influenceable behind
    # a proxy and is never used to grant access.
    #
    # Throttled before the hash comparison so this cannot be used to guess
    # the current password, and refused with the same generic message the
    # login path uses.
    if seconds_remaining("chef-password-reset", current_user.username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    if not verify_password(credentials.current_password, current_user.password):
        register_failure("chef-password-reset", current_user.username)
        audit(
            "credential_reset",
            outcome="denied",
            actor=current_user.username,
            subject=settings.CHEF_USERNAME,
            reason="reauthentication_failed",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    register_success("chef-password-reset", current_user.username)

    characters = string.ascii_letters + string.digits + "!@#$%^&*()_-+=;:[]"

    # Redrawn until it satisfies the shared policy, so the generated
    # credential is held to the same baseline as one a user chooses.
    while True:
        new_password = "".join(secrets.choice(characters) for _ in range(32))
        try:
            validate_password_policy(new_password)
            break
        except PasswordPolicyError:
            continue

    update_user_password(db, settings.CHEF_USERNAME, new_password)

    # The event, not the credential. The generated password is returned to
    # the caller once and never written anywhere else -- and the field
    # allow-list would drop it even if someone passed it here.
    audit(
        "credential_reset",
        actor=current_user.username,
        actor_role=current_user.role,
        subject=settings.CHEF_USERNAME,
        action="password_rotated",
    )

    return {"password": new_password}
