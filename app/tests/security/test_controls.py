"""Failing-closed regression tests for the critical security controls.

Each test here asserts that a specific hardening measure is present. Reverting
the corresponding fix must turn the test red, which is what makes this suite a
regression barrier rather than a functional one. Run with `pytest -m security`.
"""

import base64
import datetime
import json
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
@pytest.mark.xfail(
    strict=True,
    reason="Endpoint authorization is not implemented yet; see T7355.",
)
def test_role_change_is_not_self_service(test_db, customer_client):
    response = customer_client.put(
        "/users/update_role", json={"username": "customer", "role": "CHEF"}
    )
    assert response.status_code in (401, 403, 422)


@pytest.mark.security
@pytest.mark.xfail(
    strict=True,
    reason="Endpoint authorization is not implemented yet; see T7355.",
)
def test_delivery_orders_require_authentication(test_db, anon_client):
    assert anon_client.get("/delivery/orders").status_code in (401, 403)


# --- Object ownership ------------------------------------------------------


@pytest.mark.security
@pytest.mark.xfail(
    strict=True,
    reason="Object-level ownership checks are not implemented yet; see T7356.",
)
def test_cannot_read_another_users_order(test_db, customer_client):
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
