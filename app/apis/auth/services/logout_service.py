from datetime import datetime, timezone

from apis.auth.utils.jwt_auth import get_current_user, oauth2_scheme
from db.models import RevokedToken, User
from db.session import get_db
from fastapi import APIRouter, Depends, Response, status
from jwt_tokens import decode_token
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    """Revoke the presented token and tell the browser to drop its state.

    Logging out has to mean something server side. Without this the token
    stays valid until it expires, so "log out" on a shared machine leaves a
    working credential behind in whatever the client failed to clear.
    """
    payload = decode_token(token)

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(
        tzinfo=None
    )

    db.add(
        RevokedToken(
            jti=payload["jti"],
            revoked_at=datetime.now(),
            expires_at=expires_at,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # Already revoked. Logging out twice is not an error.
        db.rollback()

    # Cleared even though the API authenticates with a bearer header today:
    # if a cookie-based flow is ever added, a logout that quietly ignored it
    # would be the kind of gap nobody notices until it matters.
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("csrf_token", path="/")

    # Instructs the browser to drop cached pages, cookies and any local or
    # session storage for this origin, which is the part a server-side
    # revocation cannot do on its own.
    # Mutated rather than returned: returning the injected Response would
    # replace the route's 204 with that object's own unset status.
    response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'
