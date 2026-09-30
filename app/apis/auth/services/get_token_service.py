from datetime import timedelta

from apis.auth.schemas import Token
from audit_log import audit
from apis.auth.utils import authenticate_user, create_access_token
from apis.auth.utils.lockout import (
    register_failure,
    register_success,
    seconds_remaining,
)
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from rate_limiting import limiter
from sqlalchemy.orm import Session
from typing_extensions import Annotated

ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
def get_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # A locked identity gets exactly the response a wrong password gets: no
    # 429, no Retry-After, same body. Signalling the lockout would tell an
    # attacker that their guessing is being counted, when the threshold
    # trips, and when it is worth resuming. The cost is that a locked-out
    # legitimate user sees only "incorrect username or password"; they
    # recover through the password reset flow, which clears the lock.
    if seconds_remaining("login", form_data.username):
        # The username is recorded; the submitted password is not, and the
        # allow-list in audit_log drops it even if a later edit passes it.
        audit(
            "authentication",
            outcome="denied",
            actor=form_data.username,
            reason="locked_out",
        )
        raise credentials_exception

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        register_failure("login", form_data.username)
        audit(
            "authentication",
            outcome="denied",
            actor=form_data.username,
            reason="invalid_credentials",
        )
        raise credentials_exception

    register_success("login", form_data.username)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "ver": user.token_version or 0},
        expires_delta=access_token_expires,
    )
    audit("authentication", actor=user.username, actor_role=user.role)
    return Token(access_token=access_token, token_type="bearer")
