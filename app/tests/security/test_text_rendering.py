"""T7411, T7414, T89, T98, T32 — text in, text out.

The decision these tests record is that the API stores and returns text
exactly as submitted and does not HTML-encode on the way in. Encoding at
the boundary looks safer and is not: it corrupts the value for every
consumer that is not a browser (a mobile client, a kitchen printer, a CSV
export), and it produces double-encoded output the moment a consumer that
*does* escape renders it. What the API owes its consumers instead is a
declared content type, a bounded and validated value, and no HTML surface
of its own -- all three of which are asserted here.
"""

import json

import pytest

pytestmark = pytest.mark.security

PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>",
    "javascript:alert(1)",
    "'\"><script>alert(String.fromCharCode(88,83,83))</script>",
    "<iframe src=javascript:alert(1)>",
    "\u003cscript\u003ealert(1)\u003c/script\u003e",
]


def _create(client, **overrides):
    payload = {
        "name": "Soup",
        "price": 9.5,
        "category": "Starters",
        "description": "warm",
    }
    payload.update(overrides)
    return client.put("/menu", json=payload)


# --- the contract on the way in ---------------------------------------


@pytest.mark.parametrize("payload", PAYLOADS)
def test_markup_in_a_text_field_is_stored_verbatim(
    employee_client, test_db, payload
):
    """Byte for byte. If this ever starts failing because the value comes
    back encoded, the encoding was added at the wrong layer."""
    response = _create(employee_client, name=payload)

    assert response.status_code == 201
    assert response.json()["name"] == payload


@pytest.mark.parametrize("payload", PAYLOADS)
def test_markup_is_returned_unchanged_on_read(employee_client, payload):
    _create(employee_client, description=payload)

    listing = employee_client.get("/menu")

    assert listing.status_code == 200
    assert any(
        item["description"] == payload for item in listing.json()["items"]
    )


def test_the_response_declares_json_and_not_html(employee_client):
    """The header is what stops a browser rendering the stored markup: a
    payload in a JSON body is inert, the same payload served as text/html
    is not."""
    response = _create(employee_client)

    assert response.headers["content-type"].startswith("application/json")


def test_the_response_forbids_content_type_sniffing(employee_client):
    """Without nosniff, a browser may decide for itself that a JSON body
    containing markup is HTML, and the declared type stops mattering."""
    response = _create(employee_client)

    assert response.headers["x-content-type-options"] == "nosniff"


# --- the bounds the schema declares -----------------------------------


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("name", "", "empty"),
        ("name", "x" * 121, "too long"),
        ("category", "", "empty"),
        ("category", "x" * 61, "too long"),
        ("description", "x" * 2001, "too long"),
        ("price", 0, "not positive"),
        ("price", -1, "negative"),
        ("price", 100_001, "absurd"),
    ],
)
def test_a_value_outside_the_declared_contract_is_refused(
    employee_client, field, value, reason
):
    response = _create(employee_client, **{field: value})

    assert response.status_code == 422, f"{field}={reason} was accepted"


def test_an_undeclared_field_is_refused(employee_client):
    """extra="forbid": a field this model does not declare is a 422 rather
    than something a later mass assignment might pick up."""
    response = _create(employee_client, role="Chef")

    assert response.status_code == 422


def test_validation_happens_on_the_server(employee_client):
    """T32: the check is not in a client the caller controls. A payload
    that no browser form would produce still has to be refused."""
    response = employee_client.put(
        "/menu",
        content=json.dumps({"name": "x" * 500, "price": "free"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_a_refusal_does_not_echo_the_submitted_value(employee_client):
    """A 422 that quotes the payload back is a reflection point in the one
    response an attacker can always reach.

    The value is over-long as well as hostile, so the response under test is
    the refusal. A hostile value that is *within* the contract is stored and
    returned verbatim, which the tests above assert deliberately.
    """
    response = _create(employee_client, name="<script>alert(1)</script>" * 20)

    assert response.status_code == 422
    assert "<script>" not in response.text


# --- T98: the parameter that used to reach a shell --------------------


def test_an_unlisted_enum_value_is_refused_by_the_framework(chef_client):
    """The disk-stats parameter is an enum, so FastAPI refuses anything
    else before the handler runs -- validation by type rather than by a
    check someone has to remember to write."""
    response = chef_client.get("/admin/stats/disk?mount_point=/etc/passwd")

    assert response.status_code == 422


def test_the_free_text_parameter_no_longer_reaches_the_handler(chef_client):
    """`parameters` was a free-form string handed to a command builder.

    FastAPI ignores query parameters a handler does not declare, so sending
    it is a 200 rather than a 422; what matters is that it has no effect and
    that the handler cannot read it. Both are asserted -- the signature
    check is what fails if someone reintroduces the parameter.
    """
    import inspect

    from apis.admin.services import get_disk_stats_service

    with_param = chef_client.get("/admin/stats/disk?parameters=;id")
    without = chef_client.get("/admin/stats/disk")

    assert with_param.status_code == without.status_code
    assert with_param.json() == without.json()

    signature = inspect.signature(get_disk_stats_service.get_disk_usage_stats)
    assert "parameters" not in signature.parameters
