"""The subject of an operation comes from the token, not from the request.

Two related failures are pinned here. An endpoint that picks *which record*
to act on from a client-supplied key lets any caller act on anyone's record
(T128). An endpoint that decides *whether the caller may* from a client-
supplied field lets the caller answer its own authorization question (T17).
Both look like ordinary parameter handling in review, which is why they need
tests rather than a convention.
"""


import pytest
from db.models import Order, OrderStatus, User, UserRole

pytestmark = pytest.mark.security


def _other_customer(test_db) -> User:
    victim = User(
        id=901,
        username="victim",
        password="x",
        first_name="Victim",
        last_name="",
        phone_number="901901",
        role=UserRole.CUSTOMER,
    )
    test_db.add(victim)
    test_db.commit()
    return victim


def test_profile_update_key_cannot_select_another_account(test_db, customer_client):
    victim = _other_customer(test_db)

    response = customer_client.put(
        "/profile",
        json={"username": "victim", "phone_number": "666"},
    )

    assert response.status_code == 403
    test_db.refresh(victim)
    assert victim.phone_number == "901901", (
        "a caller changed another account's phone number by naming it in "
        "the request body"
    )


def test_order_id_cannot_reach_another_customers_order(test_db, customer_client):
    _other_customer(test_db)
    order = Order(
        id=9091,
        user_id=901,
        status=OrderStatus.PENDING,
        delivery_address="1 Victim Street",
        phone_number="901901",
        final_price=10.0,
    )
    test_db.add(order)
    test_db.commit()

    response = customer_client.get("/orders/9091")

    assert (
        response.status_code == 404
    ), "an order id from the URL reached a record belonging to someone else"
    assert "Victim Street" not in response.text


def test_order_list_does_not_leak_other_customers_orders(test_db, customer_client):
    _other_customer(test_db)
    test_db.add(
        Order(
            id=9092,
            user_id=901,
            status=OrderStatus.PENDING,
            delivery_address="2 Victim Street",
            phone_number="901901",
            final_price=10.0,
        )
    )
    test_db.commit()

    response = customer_client.get("/orders")

    assert response.status_code == 200
    assert "Victim Street" not in response.text


def test_registration_rejects_a_client_supplied_role(customer_client):
    """A role in the body is refused, not quietly dropped and answered 201."""
    response = customer_client.post(
        "/register",
        json={
            "username": "escalate",
            "password": "N3w-Passw0rd!x",
            "phone_number": "5550001",
            "role": "Chef",
        },
    )

    assert response.status_code == 422, (
        "registration accepted a role field; even if it is ignored today, "
        "answering 201 hides the attempt and invites a future reader to "
        "start honouring it"
    )


def test_registration_does_not_grant_a_privileged_role(test_db, anon_client):
    """And the account that is created is an ordinary customer."""
    response = anon_client.post(
        "/register",
        json={
            "username": "ordinary",
            "password": "N3w-Passw0rd!x",
            "phone_number": "5550002",
        },
    )

    assert response.status_code == 201
    created = test_db.query(User).filter(User.username == "ordinary").one()
    assert created.role == UserRole.CUSTOMER


def test_role_header_does_not_influence_authorization(customer_client):
    """A claimed role in a header is not read as an authorization input."""
    for header in ("X-User-Role", "Role", "X-Admin"):
        response = customer_client.delete("/menu/1", headers={header: "Chef"})
        assert (
            response.status_code == 403
        ), f"sending {header} changed the authorization outcome"


# --- T42: the fields written are named, not discovered -----------------


def test_the_update_helper_writes_only_the_named_profile_fields(test_db):
    """`vars(user)` copied every attribute the request model carried onto the
    columns that shared their names, so adding a field to any schema reaching
    this helper made that column writable -- and nothing in a diff of the
    helper would show it. This passes an object carrying role, password and
    token_version to prove they are ignored rather than merely absent from
    today's schemas.
    """
    from types import SimpleNamespace

    from apis.auth.utils import get_password_hash, update_user

    test_db.add(
        User(
            id=901,
            username="massassign",
            password=get_password_hash("password"),
            first_name="Before",
            last_name="",
            phone_number="9010001",
            role=UserRole.CUSTOMER,
        )
    )
    test_db.commit()

    update_user(
        test_db,
        "massassign",
        SimpleNamespace(
            username="renamed",
            first_name="After",
            role=UserRole.CHEF,
            password="anything",
            token_version=99,
            id=1,
        ),
    )

    stored = test_db.query(User).filter(User.id == 901).one()
    assert stored.first_name == "After"
    assert stored.username == "massassign"
    assert stored.role is UserRole.CUSTOMER
    assert stored.token_version != 99


def test_the_update_helper_reports_an_unknown_account(test_db):
    """It used to setattr on None, which the caller saw as a 500 rather than
    the 404 the route meant to return."""
    from apis.auth.utils import update_user

    assert update_user(test_db, "no-such-account", object()) is None
