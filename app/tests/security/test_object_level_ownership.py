"""Ownership is a query filter, never a comparison after loading.

The distinction matters more than it looks. A post-hoc check reads the row
first, so the object exists in memory, in the session, and in anything that
logs or traces the query before anyone asks whether the caller was entitled
to it — and the check is one early `return` away from being skipped. As a
filter, the row is simply never selected.

Covers the three resources named in T7356: orders, coupons and profile.
"""

import inspect
import pathlib

import pytest
from db.models import DiscountCoupon, MenuItem, Order, OrderStatus, User, UserRole

pytestmark = pytest.mark.security

VICTIM_ID = 801


@pytest.fixture
def victim(test_db) -> User:
    user = User(
        id=VICTIM_ID,
        username="victim-owner",
        password="x",
        first_name="Victim",
        last_name="",
        phone_number="801801",
        role=UserRole.CUSTOMER,
    )
    test_db.add(user)
    test_db.commit()
    return user


def test_another_users_order_is_not_readable(test_db, victim, customer_client):
    test_db.add(
        Order(
            id=8011,
            user_id=VICTIM_ID,
            status=OrderStatus.PENDING,
            delivery_address="1 Victim Lane",
            phone_number="801801",
            final_price=10.0,
        )
    )
    test_db.commit()

    assert customer_client.get("/orders/8011").status_code == 404


def test_another_users_order_status_is_not_readable(test_db, victim, customer_client):
    test_db.add(
        Order(
            id=8012,
            user_id=VICTIM_ID,
            status=OrderStatus.PENDING,
            delivery_address="2 Victim Lane",
            phone_number="801801",
            final_price=10.0,
        )
    )
    test_db.commit()

    # The real path is /orders/status/{id}; a wrong path would 404 from
    # routing and the test would pass without exercising ownership at all.
    assert customer_client.get("/orders/status/8012").status_code == 404
    assert customer_client.get("/orders/status/8012").text.count("Victim") == 0


def test_another_users_coupon_cannot_be_spent(test_db, victim, customer_client):
    """A coupon is money; redeeming someone else's is theft, not a read."""
    test_db.add(
        DiscountCoupon(
            id=8013,
            user_id=VICTIM_ID,
            discount_percentage=50,
            used=False,
        )
    )
    menu_item = MenuItem(name="Burger", price=10.0, category="Burgers")
    test_db.add(menu_item)
    test_db.commit()

    response = customer_client.post(
        "/orders",
        json={
            "delivery_address": "1 Attacker Street",
            "phone_number": "555",
            "coupon_id": 8013,
            "items": [{"menu_item_id": menu_item.id, "quantity": 1}],
        },
    )

    assert response.status_code == 404

    coupon = test_db.query(DiscountCoupon).filter(DiscountCoupon.id == 8013).one()
    assert coupon.used is False, "another user's coupon was consumed"


def test_the_coupon_list_only_returns_the_callers_own(test_db, victim, customer_client):
    test_db.add(
        DiscountCoupon(
            id=8014, user_id=VICTIM_ID, discount_percentage=90, used=False
        )
    )
    test_db.commit()

    response = customer_client.get("/discount-coupons")

    assert response.status_code == 200
    assert all(item["id"] != 8014 for item in response.json()["items"])


def test_profile_reads_resolve_to_the_caller(test_db, victim, customer_client):
    response = customer_client.get("/profile")

    assert response.status_code == 200
    assert response.json()["username"] == "customer"


def test_ownership_is_never_a_post_hoc_comparison():
    """The guard: no handler may compare user_id after loading the row.

    This is the shape the defect took in every place it was found, and it
    reads as perfectly reasonable code, so it needs a test rather than a
    convention.
    """
    app_root = pathlib.Path(__file__).resolve().parents[2]

    forbidden = (
        ".user_id != current_user.id",
        ".user_id != user.id",
        ".user_id is not current_user.id",
    )

    offenders = []
    for path in (app_root / "apis").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if pattern in text:
                offenders.append(f"{path.relative_to(app_root)}: {pattern}")

    assert offenders == [], (
        "ownership is being compared after the object was loaded; express "
        f"it as a query filter instead: {offenders}"
    )


def test_staff_access_to_another_users_record_is_an_explicit_permission():
    """Employees and chefs read the delivery feed by permission, not by luck."""
    from apis.auth.utils.authz import Permission, owned_by

    source = inspect.getsource(owned_by)

    assert "READ_DELIVERY_FEED" in source, (
        "the exemption that lets staff see other people's orders is not "
        "tied to a named permission, so it cannot be reviewed or revoked"
    )
    assert Permission.READ_DELIVERY_FEED
