"""T7355: every route makes an explicit authorization decision.

The three gaps this countermeasure closed were all of the same kind: a route
that nobody had decided about. `DELETE /menu/{id}` inherited authentication
but no role, `/delivery/orders` had neither, and `/users/update_role` let any
authenticated account grant privilege to any other.

The last test here is the one that keeps that from recurring: it walks the
live route table and fails on any route that is neither authenticated nor
named as deliberately public.
"""

import ast
import pathlib

import pytest
from db.models import MenuItem, Order, User, UserRole
from fastapi.routing import APIRoute

# Routes that are unauthenticated on purpose. Every entry is a decision
# someone made, which is the difference between this and an oversight.
PUBLIC_ROUTES = {
    ("/token", "POST"),  # issues the credential; cannot require one
    ("/register", "POST"),  # account creation
    ("/reset-password", "POST"),  # the holder cannot log in by definition
    ("/reset-password/new-password", "POST"),
    ("/menu", "GET"),  # the public menu
    ("/healthcheck", "GET"),
    ("/", "GET"),
    ("/openapi.json", "GET"),
    ("/docs", "GET"),
    ("/docs/oauth2-redirect", "GET"),
    ("/redoc", "GET"),
}

STAFF_ONLY = (
    ("delete", "/menu/{item_id}", 204),
    ("get", "/delivery/orders", 200),
)


@pytest.mark.security
def test_customer_cannot_delete_a_menu_item(test_db, customer_client):
    item = MenuItem(
        name="Taco", price=3.5, category="", description="", image_base64=""
    )
    test_db.add(item)
    test_db.commit()

    assert customer_client.delete(f"/menu/{item.id}").status_code == 403


@pytest.mark.security
def test_customer_cannot_read_the_delivery_feed(test_db, customer_client):
    """It exposes every customer's address and phone number."""
    assert customer_client.get("/delivery/orders").status_code == 403


@pytest.mark.security
def test_anonymous_cannot_read_the_delivery_feed(test_db, anon_client):
    assert anon_client.get("/delivery/orders").status_code in (401, 403)


@pytest.mark.security
def test_employee_can_read_the_delivery_feed(test_db, employee_client):
    assert employee_client.get("/delivery/orders").status_code == 200


@pytest.mark.security
def test_customer_cannot_grant_itself_a_role(test_db, customer_client):
    assert (
        customer_client.put(
            "/users/update_role",
            json={"username": "customer", "role": "Employee"},
        ).status_code
        == 403
    )


@pytest.mark.security
def test_customer_cannot_grant_another_account_a_role(test_db, customer_client):
    """The endpoint takes a username, so this was never self-service only."""
    victim = User(
        id=800,
        username="someone_else",
        password="x",
        first_name="Some",
        last_name="One",
        phone_number="555-0800",
        role=UserRole.CUSTOMER,
    )
    test_db.add(victim)
    test_db.commit()

    response = customer_client.put(
        "/users/update_role",
        json={"username": "someone_else", "role": "Employee"},
    )

    assert response.status_code == 403
    test_db.refresh(victim)
    assert victim.role == UserRole.CUSTOMER


@pytest.mark.security
def test_delivery_feed_still_returns_orders_to_staff(test_db, employee_client):
    """Guard against "fixing" authorization by breaking the feature."""
    order = Order(
        delivery_address="1 Test St",
        phone_number="555-0001",
        user_id=1,
        status="Pending",
    )
    test_db.add(order)
    test_db.commit()

    response = employee_client.get("/delivery/orders")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.security
def test_every_route_makes_an_explicit_authorization_decision(app):
    """No route may be unauthenticated without being listed as public."""
    undecided = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        dependency_names = {
            dependency.call.__name__
            for dependency in route.dependant.dependencies
            if getattr(dependency, "call", None) is not None
            and hasattr(dependency.call, "__name__")
        }
        # Requires and RolesBasedAuthChecker are class instances, so they
        # have no __name__ and are identified by their type.
        uses_role_checker = any(
            type(dependency.call).__name__ in ("Requires", "RolesBasedAuthChecker")
            for dependency in route.dependant.dependencies
            if getattr(dependency, "call", None) is not None
        )
        authenticated = uses_role_checker or bool(
            dependency_names
            & {
                "get_current_user",
                "get_current_user_pending_password_change",
            }
        )

        for method in route.methods:
            if method in ("HEAD", "OPTIONS"):
                continue
            if authenticated or (route.path, method) in PUBLIC_ROUTES:
                continue
            undecided.append(f"{method} {route.path}")

    assert undecided == [], (
        "routes with neither authentication nor an entry in PUBLIC_ROUTES: "
        f"{undecided}"
    )


# --- T85 / T2282: refusal precedes inspection of the body ----------------


@pytest.mark.security
def test_role_change_refuses_a_non_chef_before_reading_the_body(customer_client):
    """A 422 here would mean the body was parsed before the caller was judged.

    It also leaks: differing responses for a well-formed and a malformed
    body tell an unauthorized caller what the endpoint expects.
    """
    malformed = customer_client.put("/users/update_role", json={"nonsense": True})
    well_formed = customer_client.put(
        "/users/update_role", json={"username": "chef", "role": "Chef"}
    )

    assert malformed.status_code == 403, (
        "the body was validated before authorization was decided"
    )
    assert well_formed.status_code == 403
    assert malformed.json() == well_formed.json()


@pytest.mark.security
def test_the_old_debug_route_is_gone(anon_client):
    """/debug is not registered at all, not merely guarded."""
    assert anon_client.get("/debug").status_code == 404


@pytest.mark.security
def test_the_surviving_debug_route_requires_authentication(anon_client):
    assert anon_client.get("/internal/status").status_code == 401


# --- T105 / T49: no debug capability is left in the repository ---------


@pytest.mark.security
def test_the_debug_package_no_longer_exists():
    """The route was removed first; the package outlived it.

    It was mounted with include_in_schema=False, and a router nobody can see
    is where the next introspection route gets added without anyone noticing
    it is there -- the route-table guard cannot report what the schema omits.
    The one route worth keeping moved under `admin`, which is in the schema.
    """
    app_dir = pathlib.Path(__file__).resolve().parents[2]

    assert not (app_dir / "apis" / "debug").exists()

    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        assert "apis.debug" not in path.read_text(), f"{path.name} still imports it"


@pytest.mark.security
def test_no_whole_router_is_hidden_from_the_openapi_schema():
    """A hidden router and a hidden route are different risks.

    An individual route opting out is a decision about that route, and there
    are a few of those here deliberately. A *router* mounted with
    include_in_schema=False hides everything on it, including whatever is
    added to it next, which is how the /debug endpoint stayed invisible.
    """
    app_dir = pathlib.Path(__file__).resolve().parents[2]
    offenders = []

    for path in app_dir.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if name not in ("APIRouter", "include_router"):
                continue
            for keyword in node.keywords:
                if keyword.arg == "include_in_schema" and not getattr(
                    keyword.value, "value", True
                ):
                    offenders.append(
                        f"{path.relative_to(app_dir)}:{node.lineno} {name}"
                    )

    assert offenders == [], f"whole routers excluded from the schema: {offenders}"


@pytest.mark.security
def test_the_operator_status_route_returns_no_introspection(chef_client):
    """It replaced an endpoint that returned os.environ and sys.path.

    Asserted on the whole response rather than on named fields, because the
    failure worth catching is a field somebody adds later.
    """
    response = chef_client.get("/internal/status")

    assert response.status_code == 200
    assert set(response.json()) == {"status", "version"}

    body = response.text
    for leak in ("PATH", "JWT", "POSTGRES", "/Users", "site-packages", "environ"):
        assert leak not in body, f"the status response discloses {leak}"


@pytest.mark.security
def test_no_route_returns_process_or_filesystem_introspection():
    """The introspection modules must not be reachable from a handler.

    Matched on the parsed tree rather than on the text, so the explanation of
    what was removed can stay in a comment where the next reader will find
    it, instead of the comment being what fails the test.
    """
    app_dir = pathlib.Path(__file__).resolve().parents[2]
    banned = {("os", "environ"), ("sys", "path"), ("os", "listdir")}
    offenders = []

    for path in (app_dir / "apis").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if (node.value.id, node.attr) in banned:
                    offenders.append(
                        f"{path.relative_to(app_dir)}:{node.lineno} "
                        f"{node.value.id}.{node.attr}"
                    )
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in (
                "globals",
                "locals",
                "vars",
            ):
                offenders.append(
                    f"{path.relative_to(app_dir)}:{node.lineno} {node.func.id}()"
                )

    assert offenders == [], f"introspection reachable from a route: {offenders}"
