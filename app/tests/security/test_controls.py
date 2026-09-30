"""Failing-closed regression tests for the critical security controls.

Each test here asserts that a specific hardening measure is present. Reverting
the corresponding fix must turn the test red, which is what makes this suite a
regression barrier rather than a functional one. Run with `pytest -m security`.
"""

import datetime

import pytest
from config import settings
from db.models import Order, OrderStatus, User, UserRole
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
    # "alg": "none" must never be accepted, regardless of the configured algorithm.
    unsigned = jwt.encode({"sub": "chef"}, key="", algorithm="none")
    response = anon_client.get(
        "/profile", headers={"Authorization": f"Bearer {unsigned}"}
    )
    assert response.status_code == 401


# --- Endpoint authorization ------------------------------------------------


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
        "/admin/stats/disk", params={"parameters": "; echo INJECTED"}
    )
    assert response.status_code in (400, 422)
    assert "INJECTED" not in response.text


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
