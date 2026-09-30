"""Handshake policy for WebSocket routes.

No WebSocket route exists yet. This module is the policy the first one has
to use, and `tests/security/test_websocket_handshake.py` fails the build if a
route is ever added that does not.

WebSockets are worth singling out because the browser's same-origin policy
does not apply to them: any page on the internet can open a connection to
this host, and the CORS middleware guarding the HTTP routes is not consulted
during the handshake. Origin has to be checked by hand, and it has to be
checked before accept(), because once the connection is accepted the
attacker is already talking to the application.
"""

from typing import Optional

from apis.auth.utils.utils import get_user_by_username
from config import settings
from db.models import RevokedToken, User
from fastapi import WebSocket, status
from jose import JWTError
from jwt_tokens import decode_token
from sqlalchemy.orm import Session

# 1008 is "policy violation", the code the spec reserves for a handshake
# refused on grounds other than a protocol error.
POLICY_VIOLATION = status.WS_1008_POLICY_VIOLATION


def origin_is_allowed(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    # A missing Origin is refused rather than allowed. Browsers always send
    # one; a client that omits it is not a browser, and treating absence as
    # permission is how allow-lists get bypassed.
    return bool(origin) and origin in settings.ALLOWED_ORIGINS


def _bearer_token(websocket: WebSocket) -> Optional[str]:
    header = websocket.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _user_for_token(token: str, db: Session) -> Optional[User]:
    try:
        payload = decode_token(token)
    except JWTError:
        return None

    username = payload.get("sub")
    jti = payload.get("jti")
    if not username or not jti:
        return None

    if db.get(RevokedToken, jti) is not None:
        return None

    user = get_user_by_username(db, username=username)
    if user is None or payload.get("ver") != (user.token_version or 0):
        return None

    if user.must_change_password:
        return None

    return user


async def authenticate_websocket(
    websocket: WebSocket, db: Session
) -> Optional[User]:
    """Validate the handshake and return the user, or close and return None.

    Callers must treat a None return as final and send nothing further. The
    connection is closed here rather than accepted-then-closed, so an
    unauthenticated peer never reaches a state where it can send a frame.
    """
    if not origin_is_allowed(websocket):
        await websocket.close(code=POLICY_VIOLATION)
        return None

    token = _bearer_token(websocket)
    if token is None:
        await websocket.close(code=POLICY_VIOLATION)
        return None

    user = _user_for_token(token, db)
    if user is None:
        await websocket.close(code=POLICY_VIOLATION)
        return None

    return user
