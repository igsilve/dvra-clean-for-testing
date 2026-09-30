"""T15 / T226: one authorization module, and nothing deciding outside it.

The value of centralizing is only realised if nothing bypasses the centre,
so the scanning tests at the bottom matter as much as the behavioural ones
above them.
"""

import pathlib

import pytest
from apis.auth.utils.authz import (
    ROLE_PERMISSIONS,
    Permission,
    Requires,
    has_permission,
    may_use_self_service_password_reset,
    owned_by,
    permissions_for,
)
from db.models import Order, User, UserRole
from fastapi import HTTPException
from fastapi.routing import APIRoute

APP_ROOT = pathlib.Path(__file__).resolve().parents[2]
AUTHZ_MODULE = APP_ROOT / "apis" / "auth" / "utils" / "authz.py"


def _user(role, user_id=900):
    return User(id=user_id, username=f"u{user_id}", password="x", role=role)


@pytest.mark.security
def test_every_role_has_an_explicit_permission_set():
    for role in UserRole:
        assert role in ROLE_PERMISSIONS, f"{role} has no entry in ROLE_PERMISSIONS"


@pytest.mark.security
def test_an_unknown_role_gets_no_permissions():
    """Fail closed: a role with no row must not inherit anything."""
    assert permissions_for("Overlord") == set()
    assert permissions_for(None) == set()


@pytest.mark.security
def test_customers_hold_no_staff_permissions():
    customer_permissions = ROLE_PERMISSIONS[UserRole.CUSTOMER]

    for permission in (
        Permission.MANAGE_MENU,
        Permission.MANAGE_ROLES,
        Permission.READ_DISK_STATS,
        Permission.READ_DEBUG_INFO,
        Permission.RESET_CHEF_PASSWORD,
        Permission.READ_DELIVERY_FEED,
    ):
        assert permission not in customer_permissions


@pytest.mark.security
def test_employees_cannot_grant_roles_or_read_host_state():
    employee_permissions = ROLE_PERMISSIONS[UserRole.EMPLOYEE]

    assert Permission.MANAGE_ROLES not in employee_permissions
    assert Permission.READ_DISK_STATS not in employee_permissions
    assert Permission.READ_DEBUG_INFO not in employee_permissions


@pytest.mark.security
def test_requires_denies_without_the_permission():
    dependency = Requires(Permission.MANAGE_ROLES)

    with pytest.raises(HTTPException) as exc:
        dependency(_user(UserRole.CUSTOMER))

    assert exc.value.status_code == 403
    # The same opaque message for every denial; naming the missing
    # permission would tell the caller what to go after.
    assert exc.value.detail == "Unauthorized"


@pytest.mark.security
def test_requires_returns_the_user_when_permitted():
    chef = _user(UserRole.CHEF)

    assert Requires(Permission.MANAGE_ROLES)(chef) is chef


@pytest.mark.security
def test_ownership_is_applied_as_a_query_filter(test_db):
    """Not a check after loading: the row is never fetched at all."""
    owner = _user(UserRole.CUSTOMER, user_id=901)
    other = _user(UserRole.CUSTOMER, user_id=902)
    test_db.add_all([owner, other])
    test_db.commit()

    order = Order(
        delivery_address="1 St", phone_number="5", user_id=owner.id, status="Pending"
    )
    test_db.add(order)
    test_db.commit()

    assert owned_by(test_db.query(Order), Order, owner).all() == [order]
    assert owned_by(test_db.query(Order), Order, other).all() == []


@pytest.mark.security
def test_staff_are_exempt_from_the_ownership_filter(test_db):
    """Reading orders they did not place is the job."""
    customer = _user(UserRole.CUSTOMER, user_id=903)
    employee = _user(UserRole.EMPLOYEE, user_id=904)
    test_db.add_all([customer, employee])
    test_db.commit()

    order = Order(
        delivery_address="1 St",
        phone_number="5",
        user_id=customer.id,
        status="Pending",
    )
    test_db.add(order)
    test_db.commit()

    assert owned_by(test_db.query(Order), Order, employee).all() == [order]


@pytest.mark.security
def test_self_service_reset_is_limited_to_customers():
    assert may_use_self_service_password_reset(_user(UserRole.CUSTOMER))
    assert not may_use_self_service_password_reset(_user(UserRole.CHEF))
    assert not may_use_self_service_password_reset(_user(UserRole.EMPLOYEE))
    assert not may_use_self_service_password_reset(None)


@pytest.mark.security
def test_has_permission_accepts_the_stored_string_form():
    """Roles come back from the database as values, not enum members."""
    assert has_permission(_user(UserRole.CHEF.value), Permission.MANAGE_ROLES)


@pytest.mark.security
def test_no_role_comparison_exists_outside_the_authorization_module():
    """T226: a search must find role comparisons only in one module."""
    allowed = {
        AUTHZ_MODULE.resolve(),
        (APP_ROOT / "apis" / "auth" / "utils" / "roles_based_auth_checker.py").resolve(),
    }

    offenders = []
    for path in APP_ROOT.rglob("*.py"):
        if "tests" in path.parts or "migrations" in path.parts:
            continue
        if path.resolve() in allowed:
            continue
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if ".role ==" in stripped or ".role !=" in stripped:
                offenders.append(f"{path.relative_to(APP_ROOT)}:{number}")

    assert offenders == [], f"inline role comparisons outside authz: {offenders}"


@pytest.mark.security
def test_every_authorized_route_declares_a_permission(app):
    """No route may hardcode a role list at its call site."""
    offenders = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for dependency in route.dependant.dependencies:
            call = getattr(dependency, "call", None)
            if call is None:
                continue
            if type(call).__name__ == "RolesBasedAuthChecker":
                offenders.append(f"{route.path} still names roles directly")

    assert offenders == [], offenders


@pytest.mark.security
def test_adding_a_permission_touches_exactly_one_module():
    """Every Permission member is granted or withheld in ROLE_PERMISSIONS."""
    granted = set()
    for permissions in ROLE_PERMISSIONS.values():
        granted |= permissions

    orphans = [p.name for p in Permission if p not in granted]

    assert orphans == [], (
        f"permissions defined but granted to no role: {orphans}"
    )


# --- T2141 / T2142: function-level authorization, deny by default --------


@pytest.mark.security
def test_a_missing_user_is_refused_not_an_error():
    """A 500 is not a refusal; it is an accident that happened to stop it."""
    from apis.auth.utils.authz import Permission, has_permission

    assert has_permission(None, Permission.MANAGE_ROLES) is False


@pytest.mark.security
def test_a_user_without_a_role_is_refused():
    from apis.auth.utils.authz import Permission, has_permission

    class Partial:
        pass

    assert has_permission(Partial(), Permission.MANAGE_ROLES) is False


@pytest.mark.security
def test_an_unrecognised_role_grants_nothing():
    """A role added to the enum with no row in the table fails closed."""
    from apis.auth.utils.authz import permissions_for

    assert permissions_for("Superuser") == set()
    assert permissions_for(None) == set()


@pytest.mark.security
def test_every_administrative_permission_belongs_to_exactly_one_role():
    """Privilege that drifts across roles cannot be reviewed as a set."""
    from apis.auth.utils.authz import ROLE_PERMISSIONS, Permission

    administrative = {
        Permission.READ_DISK_STATS,
        Permission.READ_DEBUG_INFO,
        Permission.RESET_CHEF_PASSWORD,
        Permission.MANAGE_ROLES,
    }

    for permission in administrative:
        holders = [
            role for role, granted in ROLE_PERMISSIONS.items() if permission in granted
        ]
        assert len(holders) == 1, (
            f"{permission} is held by {holders}; an administrative "
            "capability spread across roles cannot be revoked as a set"
        )
