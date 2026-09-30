"""T7367: WebSocket handshakes must be origin-checked and authenticated.

No WebSocket route exists today, so most of these tests exercise the policy
helper directly. The last one is the one that matters over time: it fails if
a route is ever added that does not go through the helper, which is what
stops this control from quietly lapsing the moment someone ships a socket.
"""

import pathlib

import pytest
from apis.auth.utils import get_password_hash
from apis.websocket_auth import (
    POLICY_VIOLATION,
    authenticate_websocket,
    origin_is_allowed,
)
from config import settings
from db.models import RevokedToken, User, UserRole
from jwt_tokens import encode_token

ALLOWED_ORIGIN = settings.ALLOWED_ORIGINS[0]


class FakeWebSocket:
    """Minimal stand-in: the helper only reads headers and may close."""

    def __init__(self, headers):
        self.headers = headers
        self.closed_with = None
        self.accepted = False

    async def close(self, code=None):
        self.closed_with = code

    async def accept(self):
        self.accepted = True


def _make_user(test_db, user_id=700, **kwargs):
    user = User(
        id=user_id,
        username=f"socket{user_id}",
        password=get_password_hash("S0cket!Passw0rd"),
        first_name="Sock",
        last_name="Et",
        phone_number=f"555-3{user_id}",
        role=UserRole.CUSTOMER,
        **kwargs,
    )
    test_db.add(user)
    test_db.commit()
    return user


def _headers(user=None, origin=ALLOWED_ORIGIN, token=None):
    headers = {}
    if origin is not None:
        headers["origin"] = origin
    if token is None and user is not None:
        token = encode_token({"sub": user.username, "ver": user.token_version or 0})
    if token is not None:
        headers["authorization"] = f"Bearer {token}"
    return headers


@pytest.mark.security
def test_allowed_origin_passes_the_origin_check():
    assert origin_is_allowed(FakeWebSocket({"origin": ALLOWED_ORIGIN}))


@pytest.mark.security
def test_foreign_origin_fails_the_origin_check():
    assert not origin_is_allowed(FakeWebSocket({"origin": "https://evil.example"}))


@pytest.mark.security
def test_missing_origin_fails_closed():
    """Absence must not be read as permission."""
    assert not origin_is_allowed(FakeWebSocket({}))


@pytest.mark.security
@pytest.mark.asyncio
async def test_foreign_origin_is_closed_with_1008(test_db):
    user = _make_user(test_db, user_id=701)
    socket = FakeWebSocket(_headers(user, origin="https://evil.example"))

    assert await authenticate_websocket(socket, test_db) is None
    assert socket.closed_with == POLICY_VIOLATION
    assert socket.accepted is False


@pytest.mark.security
@pytest.mark.asyncio
async def test_handshake_without_a_token_is_closed(test_db):
    socket = FakeWebSocket({"origin": ALLOWED_ORIGIN})

    assert await authenticate_websocket(socket, test_db) is None
    assert socket.closed_with == POLICY_VIOLATION


@pytest.mark.security
@pytest.mark.asyncio
async def test_handshake_with_a_forged_token_is_closed(test_db):
    socket = FakeWebSocket(_headers(origin=ALLOWED_ORIGIN, token="not.a.token"))

    assert await authenticate_websocket(socket, test_db) is None
    assert socket.closed_with == POLICY_VIOLATION


@pytest.mark.security
@pytest.mark.asyncio
async def test_handshake_with_a_revoked_token_is_closed(test_db):
    user = _make_user(test_db, user_id=702)
    token = encode_token({"sub": user.username, "ver": 0})

    from jwt_tokens import decode_token

    payload = decode_token(token)
    from datetime import datetime

    test_db.add(
        RevokedToken(
            jti=payload["jti"],
            revoked_at=datetime.now(),
            expires_at=datetime.now(),
        )
    )
    test_db.commit()

    socket = FakeWebSocket(_headers(origin=ALLOWED_ORIGIN, token=token))

    assert await authenticate_websocket(socket, test_db) is None
    assert socket.closed_with == POLICY_VIOLATION


@pytest.mark.security
@pytest.mark.asyncio
async def test_handshake_with_a_stale_token_version_is_closed(test_db):
    user = _make_user(test_db, user_id=703)
    token = encode_token({"sub": user.username, "ver": 0})
    user.token_version = 1
    test_db.add(user)
    test_db.commit()

    socket = FakeWebSocket(_headers(origin=ALLOWED_ORIGIN, token=token))

    assert await authenticate_websocket(socket, test_db) is None
    assert socket.closed_with == POLICY_VIOLATION


@pytest.mark.security
@pytest.mark.asyncio
async def test_valid_handshake_returns_the_user_without_accepting(test_db):
    """The helper authenticates; accepting stays the route's decision."""
    user = _make_user(test_db, user_id=704)
    socket = FakeWebSocket(_headers(user))

    assert await authenticate_websocket(socket, test_db) is user
    assert socket.closed_with is None
    assert socket.accepted is False


@pytest.mark.security
def test_every_websocket_route_uses_the_handshake_policy():
    """The guard against this control lapsing when a socket is finally added."""
    app_root = pathlib.Path(__file__).resolve().parents[2]

    offenders = []
    for path in app_root.rglob("*.py"):
        if "tests" in path.parts or "migrations" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if ".websocket(" not in text and ".websocket_route(" not in text:
            continue
        if "authenticate_websocket" not in text:
            offenders.append(str(path.relative_to(app_root)))

    assert offenders == [], (
        "WebSocket routes that skip the handshake policy in "
        f"apis/websocket_auth.py: {offenders}"
    )
