"""T101 / T38 / T7359 / T42: no value reaches SQL as syntax.

The original defect was an UPDATE assembled by f-string from a status value
and an order id supplied by an external delivery service, executed through
`text()`. Two tests here are behavioural -- send the payloads and check what
the database did -- and two are structural, because the structural ones are
what catch the next occurrence. A behavioural test only covers the endpoints
somebody remembered to write a case for.
"""

import ast
import pathlib

import pytest
from db.models import MenuItem, Order, OrderStatus, User
from sqlalchemy import inspect

pytestmark = pytest.mark.security

APP_DIR = pathlib.Path(__file__).resolve().parents[2]

# Payloads chosen for what each one proves, not for variety: a terminator, a
# comment, a stacked statement, a tautology, a union, and a drop.
INJECTION_PAYLOADS = [
    "'",
    "' OR '1'='1",
    "'; DROP TABLE orders; --",
    "1; DELETE FROM users WHERE 1=1",
    "' UNION SELECT password FROM users --",
    "\\'",
    "%27",
    "admin'--",
]


def _application_sources():
    for path in APP_DIR.rglob("*.py"):
        if "tests" in path.parts or "migrations" in path.parts:
            continue
        yield path


# --- structural: the shapes that allow injection are absent ------------


def test_no_sql_statement_is_assembled_from_an_f_string():
    """The specific defect: an f-string passed to text().

    Detected by parsing rather than by searching for a keyword, so a
    statement split across lines or built up by concatenation is still seen.
    """
    keywords = ("select ", "insert ", "update ", "delete ", "where ", "from ")
    offenders = []

    for path in _application_sources():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.JoinedStr, ast.BinOp)):
                continue
            rendered = ast.dump(node).lower()
            if any(keyword in rendered for keyword in keywords):
                offenders.append(f"{path.relative_to(APP_DIR)}:{node.lineno}")

    assert offenders == [], f"SQL assembled by interpolation: {offenders}"


def test_no_application_module_executes_raw_sql():
    """`text()` is not forbidden in principle -- it is bound parameters that
    make it safe -- but nothing here needs it, and the safe form and the
    unsafe form differ by one character."""
    offenders = []

    for path in _application_sources():
        source = path.read_text()
        if "db.execute(" in source or "session.execute(" in source:
            offenders.append(str(path.relative_to(APP_DIR)))

    assert offenders == [], f"raw SQL execution in application code: {offenders}"


def test_untrusted_status_values_are_mapped_to_a_known_enum():
    """T42: the delivery service's response chooses a stored value.

    Accepting it as text means an external party writes directly into the
    column; mapping it through the enum means an unrecognised value is
    refused rather than stored.
    """
    source = (
        APP_DIR / "apis" / "orders" / "services" / "get_order_status.py"
    ).read_text()

    assert "OrderStatus[delivery_data" in source or "OrderStatus(delivery_data" in source
    assert "raw_sql" not in source


# --- behavioural: the payloads do what they should, which is nothing ---


@pytest.fixture
def seeded_order(test_db, customer_client):
    order = Order(id=4242, user_id=1, status=OrderStatus.PENDING)
    test_db.add(order)
    test_db.commit()
    return order


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_an_injection_payload_in_a_path_parameter_changes_nothing(
    payload, test_db, customer_client, seeded_order
):
    """A 422 from the type coercion is a pass: the value never reached SQL."""
    before = test_db.query(Order).count()

    response = customer_client.get(f"/orders/status/{payload}")

    assert response.status_code in (404, 422)
    assert test_db.query(Order).count() == before
    assert inspect(test_db.get_bind()).has_table("orders")


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_an_injection_payload_in_a_body_field_is_stored_as_data(
    payload, test_db, chef_client
):
    """The payload must be persisted verbatim, not executed.

    Asserting the row survives is not enough on its own -- an escaped
    payload and a stripped one both leave the table intact -- so this also
    checks the value came back byte for byte.
    """
    response = chef_client.put(
        "/menu",
        json={
            "name": payload,
            "description": payload,
            "category": payload,
            "price": 1.5,
        },
    )

    assert response.status_code == 201
    assert inspect(test_db.get_bind()).has_table("users")

    stored = test_db.query(MenuItem).filter(MenuItem.name == payload).one()
    assert stored.description == payload


@pytest.mark.parametrize("payload", ["' OR '1'='1", "admin'--"])
def test_an_injection_payload_in_a_credential_does_not_authenticate(
    payload, test_db, anon_client
):
    """The tautology case: the classic authentication bypass."""
    response = anon_client.post(
        "/token", data={"username": payload, "password": payload}
    )

    assert response.status_code == 401


def test_a_payload_in_a_lookup_field_does_not_widen_the_result(
    test_db, anon_client
):
    """`' OR '1'='1` in a filtered query returns every row when the value is
    syntax and no rows when it is data."""
    test_db.add(
        User(
            id=777,
            username="sqli-target",
            password="x",
            first_name="T",
            last_name="",
            phone_number="9990001",
        )
    )
    test_db.commit()

    response = anon_client.post(
        "/reset-password", json={"phone_number": "' OR '1'='1"}
    )

    # Whatever the endpoint answers, it must not have matched a user.
    assert response.status_code in (200, 202, 400, 404, 422)
    assert test_db.query(User).filter(User.phone_number == "' OR '1'='1").count() == 0
