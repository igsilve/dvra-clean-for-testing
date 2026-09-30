"""T1539 / T1540: logout must end the session server side, not just client side.

These tests use real tokens rather than the shared client fixtures, which
override get_current_user and would skip the revocation check entirely.
"""

import pytest
from apis.auth.utils import get_password_hash
from db.models import RevokedToken, User, UserRole
from jwt_tokens import encode_token

PASSWORD = "L0gout!Passw0rd"


def _make_user(test_db, username="logoutuser", user_id=500):
    user = User(
        id=user_id,
        username=username,
        password=get_password_hash(PASSWORD),
        first_name="Log",
        last_name="Out",
        phone_number=f"555-1{user_id}",
        role=UserRole.CUSTOMER,
    )
    test_db.add(user)
    test_db.commit()
    return user


def _headers(user):
    token = encode_token({"sub": user.username, "ver": user.token_version or 0})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.security
def test_token_is_unusable_after_logout(test_db, anon_client):
    user = _make_user(test_db)
    headers = _headers(user)

    assert anon_client.get("/profile", headers=headers).status_code == 200

    logout = anon_client.post("/logout", headers=headers)
    assert logout.status_code == 204

    assert anon_client.get("/profile", headers=headers).status_code == 401


@pytest.mark.security
def test_logout_expires_authentication_cookies(test_db, anon_client):
    user = _make_user(test_db, user_id=501)

    logout = anon_client.post("/logout", headers=_headers(user))

    set_cookie = logout.headers.get("set-cookie", "")
    for name in ("access_token", "csrf_token"):
        assert name in set_cookie, f"{name} was not cleared: {set_cookie!r}"
    # An expiry in the past is what actually removes the cookie; an empty
    # value alone would leave it in the jar.
    assert "expires=" in set_cookie.lower() or "max-age=0" in set_cookie.lower()


@pytest.mark.security
def test_logout_instructs_the_browser_to_clear_its_data(test_db, anon_client):
    user = _make_user(test_db, user_id=502)

    logout = anon_client.post("/logout", headers=_headers(user))

    clear = logout.headers.get("Clear-Site-Data", "")
    assert "cookies" in clear
    assert "storage" in clear
    assert "cache" in clear


@pytest.mark.security
def test_logout_records_the_revocation_with_an_expiry(test_db, anon_client):
    """The row has to be prunable, or the denylist grows without limit."""
    user = _make_user(test_db, user_id=503)

    anon_client.post("/logout", headers=_headers(user))

    revoked = test_db.query(RevokedToken).all()
    assert len(revoked) == 1
    assert revoked[0].expires_at is not None
    assert revoked[0].expires_at > revoked[0].revoked_at


@pytest.mark.security
def test_logout_does_not_end_the_accounts_other_sessions(test_db, anon_client):
    """Signing out of one device must not sign the holder out everywhere."""
    user = _make_user(test_db, user_id=504)
    first = _headers(user)
    second = _headers(user)
    assert first != second, "each token should carry its own jti"

    assert anon_client.post("/logout", headers=first).status_code == 204

    assert anon_client.get("/profile", headers=first).status_code == 401
    assert anon_client.get("/profile", headers=second).status_code == 200


@pytest.mark.security
def test_logging_out_twice_is_not_an_error(test_db, anon_client):
    user = _make_user(test_db, user_id=505)
    headers = _headers(user)

    assert anon_client.post("/logout", headers=headers).status_code == 204
    # The second call is rejected because the token is already dead, which
    # is the correct outcome and not a server error.
    assert anon_client.post("/logout", headers=headers).status_code == 401


@pytest.mark.security
def test_logout_requires_authentication(anon_client):
    assert anon_client.post("/logout").status_code == 401
