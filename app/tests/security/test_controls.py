"""Failing-closed regression tests for the critical security controls.

Each test here asserts that a specific hardening measure is present. Reverting
the corresponding fix must turn the test red, which is what makes this suite a
regression barrier rather than a functional one. Run with `pytest -m security`.
"""

import base64
import datetime
import json
import pathlib
import subprocess
from unittest import mock

import pytest
from config import settings
from apis.auth.utils import get_password_hash
from db.models import Order, OrderStatus, User, UserRole
from fastapi.testclient import TestClient
from init_app import init_app
from jose import jwt


def _forged_token(subject: str = "chef") -> str:
    """A well-formed token signed with a key the application does not hold."""
    return jwt.encode(
        {
            "sub": subject,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
        },
        "attacker-controlled-key",
        algorithm="HS256",
    )


# --- JWT verification ------------------------------------------------------


@pytest.mark.security
def test_forged_jwt_is_rejected(test_db, anon_client):
    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {_forged_token()}"}
    )
    assert response.status_code == 401


@pytest.mark.security
def test_unsigned_alg_none_jwt_is_rejected(test_db, anon_client):
    # "alg": "none" must never be accepted, regardless of the configured
    # algorithm. The token is assembled by hand because python-jose refuses
    # to *produce* an unsigned token, while an attacker is under no such
    # constraint -- they just concatenate the segments themselves.
    def b64(payload):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    header = b64({"alg": "none", "typ": "JWT"})
    claims = b64(
        {
            "sub": "chef",
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=30)
                ).timestamp()
            ),
        }
    )
    unsigned = f"{header}.{claims}."

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {unsigned}"}
    )
    assert response.status_code == 401


# --- Endpoint authorization ------------------------------------------------


@pytest.mark.security
def test_jwt_without_an_exp_claim_is_rejected(test_db, anon_client):
    """A token omitting exp must not be treated as non-expiring.

    verify_exp only checks an exp that is present, so the decode options must
    also *require* it. python-jose spells that as require_exp and silently
    ignores unknown option keys, so a PyJWT-style {"require": [...]} would
    leave this hole open.
    """
    forever = jwt.encode(
        {"sub": "chef"}, settings.JWT_SECRET_KEY, algorithm="HS256"
    )

    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {forever}"}
    )
    assert response.status_code == 401


@pytest.mark.security
def test_admin_endpoints_reject_anonymous(test_db, anon_client):
    assert anon_client.get("/admin/stats/disk").status_code == 401
    assert anon_client.post("/admin/reset-chef-password").status_code == 401


@pytest.mark.security
def test_role_change_is_not_self_service(test_db, customer_client):
    response = customer_client.put(
        "/users/update_role", json={"username": "customer", "role": "CHEF"}
    )
    assert response.status_code in (401, 403, 422)


@pytest.mark.security
def test_delivery_orders_require_authentication(test_db, anon_client):
    assert anon_client.get("/delivery/orders").status_code in (401, 403)


# --- Object ownership ------------------------------------------------------


@pytest.mark.security
def test_cannot_read_another_users_order(test_db, customer_client):
    """Ownership is now enforced on the single-order lookup (T106).

    This carried a strict xfail deferring to T7356. The fix landed with
    T106 and the test XPASSed, so the marker is gone. T7356 still owns the
    wider sweep of object-level checks across other resources.
    """
    owner = User(
        id=99,
        username="someone-else",
        password="x",
        first_name="Other",
        last_name="",
        phone_number="999",
        role=UserRole.CUSTOMER,
    )
    other_order = Order(
        id=4242,
        user_id=99,
        status=OrderStatus.PENDING,
        delivery_address="1 Other Street",
        phone_number="999",
        final_price=10.0,
    )
    test_db.add(owner)
    test_db.add(other_order)
    test_db.commit()

    # customer_client is user id 3, so order 4242 belongs to someone else.
    response = customer_client.get("/orders/4242")
    assert response.status_code in (403, 404)


# --- Command execution -----------------------------------------------------


@pytest.mark.security
def test_disk_stats_does_not_execute_injected_commands(test_db, chef_client):
    response = chef_client.get(
        "/admin/stats/disk", params={"mount_point": "; echo INJECTED"}
    )
    assert response.status_code in (400, 422)
    assert "INJECTED" not in response.text


@pytest.mark.security
def test_disk_stats_errors_do_not_leak_command_detail(test_db, chef_client):
    """A failing df must not return the command string, a path or a traceback."""
    with mock.patch(
        "apis.admin.utils.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, ["df", "-h", "/"]),
    ):
        response = chef_client.get("/admin/stats/disk", params={"mount_point": "/"})

    assert response.status_code == 500
    body = response.text
    assert "df" not in body
    assert "Traceback" not in body
    assert response.json()["detail"] == "Unable to read disk statistics"


# --- CORS ------------------------------------------------------------------


@pytest.mark.security
def test_cors_does_not_reflect_arbitrary_origin(test_db, anon_client):
    response = anon_client.get(
        "/healthcheck", headers={"Origin": "https://attacker.example"}
    )
    allowed = response.headers.get("access-control-allow-origin")
    assert allowed != "https://attacker.example"
    assert allowed != "*"


@pytest.mark.security
def test_cors_never_pairs_wildcard_with_credentials(test_db, anon_client):
    response = anon_client.options(
        "/healthcheck",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    if response.headers.get("access-control-allow-credentials") == "true":
        assert response.headers.get("access-control-allow-origin") != "*"


# --- Transport and response hardening --------------------------------------


@pytest.mark.security
def test_untrusted_host_header_is_rejected(test_db, anon_client):
    response = anon_client.get("/healthcheck", headers={"Host": "attacker.example"})
    assert response.status_code == 400


@pytest.mark.security
def test_security_headers_are_present(test_db, anon_client):
    headers = anon_client.get("/healthcheck").headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "content-security-policy" in headers
    assert "x-powered-by" not in headers


@pytest.mark.security
def test_debug_endpoint_does_not_leak_environment(test_db, anon_client):
    response = anon_client.get("/debug")
    assert response.status_code == 404


@pytest.mark.security
def test_interactive_docs_are_withdrawn_in_production():
    """/, /docs, /redoc and /openapi.json must all 404 when ENV=production.

    The app is rebuilt here rather than reusing the session client, because
    the environment is read when the application is constructed.
    """
    from config import ENV
    from main import setup_static_files_and_docs

    with mock.patch.object(settings, "ENVIRONMENT", ENV.PRODUCTION):
        prod_app = init_app()
        setup_static_files_and_docs(prod_app)

    with TestClient(prod_app) as client:
        for path in ("/", "/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404, path


@pytest.mark.security
def test_interactive_docs_are_available_outside_production(test_db):
    """The guard must be environment-specific, not a blanket removal.

    The shared `app` fixture calls only `init_app()`, so the docs routes are
    not registered on it; this builds an app the same way `main` does.
    """
    from main import setup_static_files_and_docs

    dev_app = init_app()
    setup_static_files_and_docs(dev_app)

    with TestClient(dev_app) as client:
        for path in ("/", "/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 200, path


@pytest.mark.security
def test_cookie_authenticated_state_change_requires_csrf_token(test_db, anon_client):
    # Guards against a future move to cookie auth: once a request carries an
    # auth cookie, an unsafe method without a matching token is refused.
    response = anon_client.patch(
        "/profile", json={"username": "someone"}, cookies={"access_token": "whatever"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF token missing or invalid"

    mismatched = anon_client.patch(
        "/profile",
        json={"username": "someone"},
        cookies={"access_token": "whatever", "csrf_token": "aaa"},
        headers={"X-CSRF-Token": "bbb"},
    )
    assert mismatched.status_code == 403


@pytest.mark.security
def test_token_endpoint_does_not_set_an_authentication_cookie(test_db, anon_client):
    """The token stays out of cookies, which is what removes the CSRF surface.

    If a future change starts setting an auth cookie here, this test fails and
    the attributes-plus-CSRF-token requirements become live.
    """
    test_db.add(
        User(
            id=210,
            username="cookiecheck",
            password=get_password_hash("password"),
            first_name="Cookie",
            last_name="",
            phone_number="2100",
            role=UserRole.CUSTOMER,
        )
    )
    test_db.commit()

    response = anon_client.post(
        "/token", data={"username": "cookiecheck", "password": "password"}
    )

    assert response.status_code == 200
    assert "set-cookie" not in {name.lower() for name in response.headers}
    assert response.json()["access_token"]


@pytest.mark.security
def test_any_authentication_cookie_must_be_httponly_secure_and_samesite(
    test_db, anon_client
):
    """Guard the attributes for whenever an auth cookie does get introduced."""
    test_db.add(
        User(
            id=211,
            username="cookieattrs",
            password=get_password_hash("password"),
            first_name="Cookie",
            last_name="",
            phone_number="2101",
            role=UserRole.CUSTOMER,
        )
    )
    test_db.commit()

    response = anon_client.post(
        "/token", data={"username": "cookieattrs", "password": "password"}
    )

    for header in response.headers.get_list("set-cookie"):
        if not any(
            header.lower().startswith(f"{name}=")
            for name in ("access_token", "session", "session_id")
        ):
            continue
        lowered = header.lower()
        assert "httponly" in lowered, header
        assert "secure" in lowered, header
        assert "samesite=" in lowered, header


@pytest.mark.security
def test_cross_site_form_post_to_a_state_changing_route_fails(test_db, anon_client):
    """A browser form POST from another origin carries no Authorization header."""
    response = anon_client.post(
        "/apply-referral",
        json={"referral_code": "ABC12345"},
        headers={
            "Origin": "https://attacker.example",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    assert response.status_code == 401


@pytest.mark.security
def test_bearer_only_requests_are_not_blocked_by_csrf(test_db, customer_client):
    # No auth cookie, so the CSRF check must stay out of the way entirely.
    response = customer_client.patch("/profile", json={"first_name": "Ada"})
    assert response.status_code != 403


@pytest.mark.security
def test_validation_errors_do_not_echo_submitted_input(test_db, anon_client):
    secret = "Sup3rSecretPassw0rd!"

    # phone_number is required, so this fails validation while carrying a
    # password. The rejected values must not come back in the response.
    response = anon_client.post(
        "/register", json={"username": "someone", "password": secret}
    )

    assert response.status_code == 422
    assert secret not in response.text
    assert "someone" not in response.text

    body = response.json()
    assert body["detail"] == "Request validation failed"
    for error in body["errors"]:
        assert set(error) == {"loc", "type"}


@pytest.mark.security
def test_oversized_page_request_is_rejected(test_db, customer_client):
    # Rejected outright rather than clamped, so a caller cannot probe for the
    # effective ceiling by watching where the response size stops growing.
    response = customer_client.get("/orders", params={"limit": 100000})
    assert response.status_code == 422

    assert customer_client.get("/orders", params={"limit": 0}).status_code == 422
    assert customer_client.get("/orders", params={"skip": -1}).status_code == 422


@pytest.mark.security
def test_collection_responses_are_not_top_level_arrays(test_db, anon_client):
    # A bare top-level JSON array is script-includable; an object envelope is
    # not. Applies even to non-sensitive collections, so the shape cannot
    # regress once the data becomes sensitive.
    response = anon_client.get("/menu")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers.get("x-content-type-options") == "nosniff"

    body = response.json()
    assert isinstance(body, dict)
    assert isinstance(body["items"], list)


@pytest.mark.security
def test_security_headers_survive_middleware_short_circuits(test_db, anon_client):
    # Layers below SecurityHeadersMiddleware answer without reaching a route.
    # Their replies must still carry the headers, which only holds while
    # SecurityHeadersMiddleware is the outermost layer.
    oversized = anon_client.post(
        "/register", json={"description": "A" * (settings.MAX_BODY_BYTES + 1024)}
    )
    assert oversized.status_code == 413
    assert oversized.headers.get("X-Frame-Options") == "DENY"
    assert "frame-ancestors 'none'" in oversized.headers.get(
        "content-security-policy", ""
    )

    bad_host = anon_client.get("/healthcheck", headers={"Host": "attacker.example"})
    assert bad_host.status_code == 400
    assert bad_host.headers.get("X-Frame-Options") == "DENY"


# --- JWT handling centralization -------------------------------------------


@pytest.mark.security
def test_jwt_algorithm_is_defined_in_exactly_one_place():
    """Three copies of the algorithm were three chances to loosen one.

    Guards against a verifying path being reintroduced with its own
    constant, which could drift from the algorithm used to sign.
    """
    import pathlib

    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []
    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts or path.name == "jwt_tokens.py":
            continue
        text = path.read_text()
        if "HS256" in text or "algorithms=[" in text:
            offenders.append(str(path.relative_to(app_dir)))

    assert offenders == [], f"JWT algorithm referenced outside jwt_tokens.py: {offenders}"


@pytest.mark.security
def test_token_issuance_and_verification_agree():
    """A token minted by the issuing path must satisfy the verifying path."""
    from jwt_tokens import decode_token
    from apis.auth.utils import create_access_token

    claims = decode_token(create_access_token({"sub": "roundtrip"}))

    assert claims["sub"] == "roundtrip"
    assert "exp" in claims


@pytest.mark.security
def test_issued_tokens_always_carry_an_expiry():
    """Even when the caller passes no expiry, exp must be set."""
    from jwt_tokens import DECODE_OPTIONS, decode_token
    from apis.auth.utils import create_access_token

    assert DECODE_OPTIONS["require_exp"] is True
    assert DECODE_OPTIONS["require_sub"] is True
    assert DECODE_OPTIONS["verify_signature"] is True

    # Would raise if exp were absent, since decoding requires it.
    assert decode_token(create_access_token({"sub": "noexpiry"}))["exp"]


# --- T281 / T284: the token carries a full claim set and a bounded life ---


@pytest.mark.security
@pytest.mark.parametrize("claim", ("iat", "exp", "jti", "iss", "aud"))
def test_every_issued_token_carries_the_full_claim_set(claim):
    """exp alone identifies nothing.

    Without iss and aud a token minted for another service verifies here
    whenever the two share a key; without jti two tokens for the same user in
    the same second are indistinguishable, so neither a log nor a revocation
    list can name one of them.
    """
    from jwt_tokens import DECODE_OPTIONS, decode_token
    from apis.auth.utils import create_access_token

    claims = decode_token(create_access_token({"sub": "claims"}))

    assert claim in claims
    # Present is not the same as checked: a token minted before the claim
    # existed would still be accepted unless its presence is required.
    assert DECODE_OPTIONS[f"require_{claim}"] is True


@pytest.mark.security
def test_two_tokens_for_the_same_user_are_distinguishable():
    """iat has one-second resolution, so it cannot do this on its own."""
    from jwt_tokens import decode_token
    from apis.auth.utils import create_access_token

    first = decode_token(create_access_token({"sub": "same"}))
    second = decode_token(create_access_token({"sub": "same"}))

    assert first["jti"] != second["jti"]


@pytest.mark.security
def test_a_caller_cannot_ask_for_a_longer_lifetime_than_the_ceiling():
    """The lifetime is the whole exposure window of a stateless credential.

    A call site passing a generous timedelta, or one computed from a request,
    is how a fifteen-minute token quietly becomes a permanent one. The cap is
    applied at issuance rather than trusted to the caller.
    """
    from datetime import datetime, timedelta, timezone

    from jwt_tokens import MAX_EXPIRY, decode_token, encode_token

    claims = decode_token(encode_token({"sub": "greedy"}, timedelta(days=365)))
    lifetime = datetime.fromtimestamp(claims["exp"], timezone.utc) - datetime.now(
        timezone.utc
    )

    assert lifetime <= MAX_EXPIRY
    assert MAX_EXPIRY <= timedelta(hours=1)


@pytest.mark.security
def test_a_shorter_lifetime_is_still_honoured():
    """The cap must be a ceiling, not a floor that lengthens short tokens."""
    from datetime import datetime, timedelta, timezone

    from jwt_tokens import decode_token, encode_token

    claims = decode_token(encode_token({"sub": "brief"}, timedelta(minutes=2)))
    lifetime = datetime.fromtimestamp(claims["exp"], timezone.utc) - datetime.now(
        timezone.utc
    )

    assert lifetime <= timedelta(minutes=2)


@pytest.mark.security
def test_issued_tokens_can_be_revoked_before_they_expire():
    """Otherwise a stolen token stays valid for its full life regardless of
    what happens to the account, which is the cost of statelessness."""
    from db.models import User
    from jwt_tokens import invalidate_issued_tokens

    user = User(id=999, username="revoked", token_version=3)
    invalidate_issued_tokens(user)

    assert user.token_version == 4


# --- T1468: nothing sensitive is left at rest in the browser ------------


@pytest.mark.security
def test_no_client_side_code_stores_a_credential_in_web_storage():
    """There is no browser client in this repository, and the token is
    delivered in a response body rather than a cookie, so today nothing is
    at rest in a browser at all.

    This fails the moment client-side code appears that puts a credential
    into localStorage or sessionStorage, which is the specific mistake this
    control exists to prevent and the one that survives a code review
    because it looks like ordinary state management.
    """
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    tracked = subprocess.run(
        ["git", "ls-files", "*.js", "*.jsx", "*.ts", "*.tsx", "*.html", "*.vue"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout.split()

    offenders = []
    for relative in tracked:
        source = (repo_root / relative).read_text(encoding="utf-8", errors="ignore")
        for storage in ("localStorage", "sessionStorage"):
            if storage not in source:
                continue
            for name in ("token", "Token", "password", "secret", "jwt"):
                if name in source:
                    offenders.append(f"{relative}: {storage} near '{name}'")
                    break

    assert offenders == [], f"credentials placed in web storage: {offenders}"


@pytest.mark.security
def test_the_credential_lifetime_is_measured_in_minutes():
    """A long-lived token is a long-lived liability wherever the client
    happens to keep it, which the server cannot see and cannot revoke
    before expiry."""
    from apis.auth.services.get_token_service import ACCESS_TOKEN_EXPIRE_MINUTES

    assert 0 < ACCESS_TOKEN_EXPIRE_MINUTES <= 60


@pytest.mark.security
def test_credential_responses_are_not_cacheable(test_db, anon_client):
    """A cached response is the credential at rest in the browser's disk
    cache, which no client-side discipline can undo."""
    test_db.add(
        User(
            id=211,
            username="cachecheck",
            password=get_password_hash("password"),
            first_name="Cache",
            last_name="",
            phone_number="2110",
            role=UserRole.CUSTOMER,
        )
    )
    test_db.commit()

    response = anon_client.post(
        "/token", data={"username": "cachecheck", "password": "password"}
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"


# --- T21: data in transit --------------------------------------------


@pytest.mark.security
@pytest.mark.parametrize(
    "mode", ["disable", "allow", "prefer", "", "REQUIRE", "nonsense"]
)
def test_a_database_mode_that_can_fall_back_to_plaintext_is_refused(
    monkeypatch, mode
):
    """`prefer` is the dangerous one: it encrypts when the server offers
    TLS and connects in the clear when it does not, so a server that
    silently stopped serving certificates looks healthy."""
    monkeypatch.setattr(type(settings), "DB_BACKEND", "postgres")
    monkeypatch.setattr(type(settings), "POSTGRES_SSLMODE", mode)

    with pytest.raises(RuntimeError, match="POSTGRES_SSLMODE"):
        settings.DATABASE_URL


@pytest.mark.security
def test_the_database_connection_requires_tls_by_default(monkeypatch):
    monkeypatch.setattr(type(settings), "DB_BACKEND", "postgres")

    assert settings.DATABASE_URL.query["sslmode"] == "require"


@pytest.mark.security
def test_a_supplied_ca_upgrades_the_connection_to_authenticate_the_server(
    monkeypatch,
):
    """`require` encrypts to whoever answered; only verify-full checks that
    whoever answered is the database."""
    monkeypatch.setattr(type(settings), "DB_BACKEND", "postgres")
    monkeypatch.setattr(type(settings), "POSTGRES_SSLROOTCERT", "/etc/pg/ca.crt")

    url = settings.DATABASE_URL

    assert url.query["sslmode"] == "verify-full"
    assert url.query["sslrootcert"] == "/etc/pg/ca.crt"


# --- T2599 / T2608: connection string parameter pollution ------------


@pytest.mark.security
@pytest.mark.parametrize(
    "password",
    [
        "p@ss/word?x=1",
        # Each of these is a delimiter that used to be read as structure.
        "pass@evil.example.com",
        "pass?host=evil.example.com",
        "pass/otherdb",
        "pass#fragment",
        "pass word",
    ],
)
def test_a_password_cannot_rewrite_any_part_of_the_connection(
    monkeypatch, password
):
    """The credential must not be able to decide where the credential goes.

    An interpolated password containing `@` moves the host; one containing
    `?host=` appends a connection parameter, and libpq takes the later
    occurrence, so the value being protected chooses the server it is sent
    to. Asserted on the parsed components rather than on the rendered string,
    because that is what actually reaches the driver.
    """
    monkeypatch.setattr(type(settings), "DB_BACKEND", "postgres")
    monkeypatch.setattr(type(settings), "POSTGRES_SERVER", "db.internal")
    monkeypatch.setattr(type(settings), "POSTGRES_DB", "restaurant")
    monkeypatch.setattr(type(settings), "POSTGRES_PASSWORD", password)

    url = settings.DATABASE_URL

    assert url.host == "db.internal"
    assert url.database == "restaurant"
    assert url.port == 5432
    # The delimiter stayed inside the value instead of becoming structure.
    assert url.password == password
    assert set(url.query) == {"sslmode"}


@pytest.mark.security
@pytest.mark.parametrize("component", ["POSTGRES_USER", "POSTGRES_DB"])
def test_no_other_component_can_inject_connection_parameters(
    monkeypatch, component
):
    """The password is the usual suspect, but every component was interpolated."""
    monkeypatch.setattr(type(settings), "DB_BACKEND", "postgres")
    monkeypatch.setattr(type(settings), "POSTGRES_SERVER", "db.internal")
    monkeypatch.setattr(type(settings), component, "x?host=evil.example.com")

    url = settings.DATABASE_URL

    assert url.host == "db.internal"
    assert set(url.query) == {"sslmode"}


@pytest.mark.security
def test_the_rendered_url_does_not_expose_the_password(monkeypatch):
    """Anything that logs the connection URL logs whatever str() returns."""
    monkeypatch.setattr(type(settings), "DB_BACKEND", "postgres")
    monkeypatch.setattr(type(settings), "POSTGRES_PASSWORD", "s3cret-value")

    assert "s3cret-value" not in str(settings.DATABASE_URL)
    # Still reachable for the driver, which is given the object, not the text.
    assert settings.DATABASE_URL.password == "s3cret-value"
