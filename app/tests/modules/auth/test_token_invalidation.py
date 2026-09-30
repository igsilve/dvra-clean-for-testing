"""Tokens issued before a credential or privilege change must stop working.

The application authenticates with stateless JWTs, so there is no server-side
session entry to delete on login. The equivalent guarantee is provided by a
per-user token_version stamped into each token and compared on every request.
"""

import pytest
from apis.auth.utils import get_password_hash, update_user_password
from db.models import User, UserRole


def _make_user(test_db, user_id, username, phone, role=UserRole.CUSTOMER):
    user = User(
        id=user_id,
        username=username,
        password=get_password_hash("password"),
        first_name="Test",
        last_name="",
        phone_number=phone,
        role=role,
    )
    test_db.add(user)
    test_db.commit()
    return user


def _login(client, username, password="password"):
    response = client.post(
        "/token", data={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_new_accounts_start_at_token_version_zero(test_db):
    user = _make_user(test_db, 300, "versionzero", "3000")

    assert user.token_version == 0


def test_issued_token_authenticates_before_any_change(test_db, anon_client):
    _make_user(test_db, 301, "stillvalid", "3001")
    token = _login(anon_client, "stillvalid")

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200


def test_password_change_revokes_tokens_issued_earlier(test_db, anon_client):
    _make_user(test_db, 302, "rotatepw", "3002")
    token = _login(anon_client, "rotatepw")

    update_user_password(test_db, "rotatepw", "a-brand-new-password")
    test_db.commit()

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_a_token_issued_after_the_change_works(test_db, anon_client):
    """Revocation must not be permanent: re-authenticating restores access."""
    _make_user(test_db, 303, "reissue", "3003")
    _login(anon_client, "reissue")

    update_user_password(test_db, "reissue", "a-brand-new-password")
    test_db.commit()

    fresh = _login(anon_client, "reissue", password="a-brand-new-password")
    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {fresh}"}
    )

    assert response.status_code == 200


def test_revocation_is_scoped_to_the_affected_account(test_db, anon_client):
    _make_user(test_db, 304, "victim", "3004")
    _make_user(test_db, 305, "bystander", "3005")
    bystander_token = _login(anon_client, "bystander")

    update_user_password(test_db, "victim", "a-brand-new-password")
    test_db.commit()

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {bystander_token}"}
    )

    assert response.status_code == 200


def test_a_token_without_a_version_claim_is_refused(test_db, anon_client):
    """The check fails closed for tokens minted before it existed."""
    from jwt_tokens import encode_token

    _make_user(test_db, 306, "legacytoken", "3006")
    legacy = encode_token({"sub": "legacytoken"})

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {legacy}"}
    )

    assert response.status_code == 401


@pytest.mark.parametrize("forged_version", [1, 99, -1])
def test_a_token_with_a_mismatched_version_is_refused(
    test_db, anon_client, forged_version
):
    from jwt_tokens import encode_token

    _make_user(test_db, 307 + abs(forged_version), f"forged{forged_version}", f"31{abs(forged_version)}")
    forged = encode_token(
        {"sub": f"forged{forged_version}", "ver": forged_version}
    )

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {forged}"}
    )

    assert response.status_code == 401


# --- Token identity and claim set (T86) ------------------------------------


def test_every_token_carries_jti_iat_iss_and_aud(test_db, anon_client):
    from jose import jwt as jose_jwt

    from config import settings

    _make_user(test_db, 320, "claimset", "3200")
    token = _login(anon_client, "claimset")

    claims = jose_jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=["HS256"],
        audience=settings.JWT_AUDIENCE,
        issuer=settings.JWT_ISSUER,
    )

    assert claims["jti"]
    assert claims["iat"]
    assert claims["iss"] == settings.JWT_ISSUER
    assert claims["aud"] == settings.JWT_AUDIENCE


def test_two_tokens_for_the_same_user_are_never_identical(test_db, anon_client):
    """iat has one-second resolution, so jti is what guarantees uniqueness."""
    from jwt_tokens import encode_token

    _make_user(test_db, 321, "unique", "3201")

    tokens = {encode_token({"sub": "unique", "ver": 0}) for _ in range(25)}

    assert len(tokens) == 25


def test_jti_is_unique_across_issued_tokens(test_db):
    from jose import jwt as jose_jwt

    from config import settings
    from jwt_tokens import encode_token

    jtis = set()
    for _ in range(25):
        claims = jose_jwt.decode(
            encode_token({"sub": "jticheck", "ver": 0}),
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        jtis.add(claims["jti"])

    assert len(jtis) == 25


def test_a_token_from_another_issuer_is_rejected(test_db, anon_client):
    import datetime

    from jose import jwt as jose_jwt

    from config import settings

    _make_user(test_db, 322, "wrongiss", "3202")
    foreign = jose_jwt.encode(
        {
            "sub": "wrongiss",
            "ver": 0,
            "jti": "abc",
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "iss": "some-other-service",
            "aud": settings.JWT_AUDIENCE,
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {foreign}"}
    )
    assert response.status_code == 401


def test_a_token_for_another_audience_is_rejected(test_db, anon_client):
    import datetime

    from jose import jwt as jose_jwt

    from config import settings

    _make_user(test_db, 323, "wrongaud", "3203")
    foreign = jose_jwt.encode(
        {
            "sub": "wrongaud",
            "ver": 0,
            "jti": "abc",
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "iss": settings.JWT_ISSUER,
            "aud": "a-different-application",
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {foreign}"}
    )
    assert response.status_code == 401
