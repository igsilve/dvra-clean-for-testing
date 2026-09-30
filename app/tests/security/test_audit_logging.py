"""T7371, T349, T350 — the audit trail and what it must not carry.

Two properties are tested together throughout, because either one on its
own is worse than nothing: a record must exist for every security-relevant
event, and no record may carry a credential. A trail with gaps cannot
answer an incident review; a trail full of passwords is a second copy of
the credential store in a system with weaker access control.
"""

import json
import logging

import pytest
from audit_log import (
    ALLOWED_FIELDS,
    SENSITIVE_FIELD_MARKERS,
    JsonFormatter,
    audit,
    configure_logging,
    redact,
)

pytestmark = pytest.mark.security


@pytest.fixture
def captured_audit(caplog):
    """The audit records emitted during a test, as dictionaries."""
    caplog.set_level(logging.INFO)

    def records():
        formatter = JsonFormatter()
        out = []
        for record in caplog.records:
            if getattr(record, "audit", None) is None:
                continue
            out.append(json.loads(formatter.format(record)))
        return out

    return records


# --- the redaction contract -------------------------------------------


@pytest.mark.parametrize(
    "field",
    [
        "password",
        "new_password",
        "current_password",
        "POSTGRES_PASSWORD",
        "jwt_secret_key",
        "access_token",
        "authorization",
        "session_cookie",
        "api_key",
        "otp",
        "reset_code",
        "hmac_key",
        "private_key",
    ],
)
def test_a_field_that_looks_like_a_secret_is_dropped(field):
    """Matched as substrings, so `new_password` and `password_confirm` are
    both covered without anyone having to enumerate them."""
    result = redact({field: "the-actual-value"})

    assert "the-actual-value" not in json.dumps(result)


def test_a_dropped_field_is_reported_as_withheld():
    """A reader has to be able to tell "nothing was sent" from "something
    was sent and withheld"; silence conflates the two."""
    result = redact({"password": "hunter2", "actor": "alice"})

    assert result["withheld_fields"] == ["password"]
    assert result["actor"] == "alice"


def test_a_secret_is_dropped_rather_than_masked():
    """A masked value still discloses the length, and a truncated one is
    often still usable."""
    result = redact({"password": "a" * 64})
    serialized = json.dumps(result)

    assert "a" * 8 not in serialized
    assert "64" not in serialized
    assert "*" not in serialized


def test_an_unrecognised_field_is_dropped_by_default():
    """An allow-list, not a deny-list: a new caller passing something
    sensitive under an unfamiliar name should be dropped, not admitted."""
    result = redact({"actor": "alice", "something_new": "value"})

    assert result == {"actor": "alice"}


def test_every_marker_is_lowercase():
    """Matching lowercases the field name, so an uppercase marker would
    never match anything -- a control that silently does nothing."""
    assert all(marker.islower() for marker in SENSITIVE_FIELD_MARKERS)


def test_no_allowed_field_name_collides_with_a_marker():
    """Otherwise an allowed field would be dropped as a suspected secret
    and the trail would lose data it is meant to carry."""
    for field in ALLOWED_FIELDS:
        for marker in SENSITIVE_FIELD_MARKERS:
            assert marker not in field.lower(), f"{field} matches {marker}"


# --- the record format -------------------------------------------------


def test_each_record_is_one_json_object():
    """Plain text makes the trail expensive to query and forgeable: a
    newline in a field would otherwise start a second record."""
    record = logging.LogRecord(
        "audit", logging.INFO, __file__, 1, "evt", None, None
    )
    record.audit = {"event": "evt", "actor": "alice\nfabricated: true"}

    line = JsonFormatter().format(record)

    assert "\n" not in line
    parsed = json.loads(line)
    assert parsed["actor"] == "alice\nfabricated: true"


def test_a_record_carries_a_timestamp_level_and_event():
    record = logging.LogRecord(
        "audit", logging.INFO, __file__, 1, "authentication", None, None
    )
    record.audit = {"event": "authentication", "outcome": "denied"}

    parsed = json.loads(JsonFormatter().format(record))

    assert parsed["timestamp"]
    assert parsed["level"] == "INFO"
    assert parsed["event"] == "authentication"
    assert parsed["outcome"] == "denied"


def test_a_logged_exception_carries_no_traceback():
    """File paths and local variables in a shared log store are their own
    disclosure."""
    try:
        raise ValueError("the message")
    except ValueError:
        import sys

        record = logging.LogRecord(
            "audit", logging.ERROR, __file__, 1, "failed", None, sys.exc_info()
        )

    parsed = json.loads(JsonFormatter().format(record))

    assert parsed["error"] == "ValueError"
    assert "Traceback" not in json.dumps(parsed)
    assert __file__ not in json.dumps(parsed)


def test_configuring_logging_twice_does_not_duplicate_records():
    """A test runner that builds the app more than once would otherwise
    write every line as many times as the factory ran."""
    configure_logging()
    configure_logging()

    assert len(logging.getLogger().handlers) == 1


def test_every_record_has_an_outcome(captured_audit):
    """A trail of events with no outcomes cannot answer the only question
    anyone asks of it."""
    audit("some_event")
    audit("another_event", outcome="denied")

    records = captured_audit()

    assert [r["outcome"] for r in records] == ["success", "denied"]


# --- the events that must exist ---------------------------------------


def test_a_failed_login_is_recorded(anon_client, captured_audit):
    anon_client.post(
        "/token",
        data={"username": "nobody@example.com", "password": "wrong-password"},
    )

    events = [r for r in captured_audit() if r["event"] == "authentication"]

    assert events, "a failed login left no record"
    assert events[0]["outcome"] == "denied"
    assert events[0]["actor"] == "nobody@example.com"
    assert "wrong-password" not in json.dumps(events)


def test_a_successful_login_is_recorded(anon_client, test_db, captured_audit):
    from db.models import User, UserRole

    from apis.auth.utils import get_password_hash

    test_db.add(
        User(
            id=99,
            username="auditee",
            password=get_password_hash("Correct-Horse-9-Battery"),
            first_name="A",
            last_name="B",
            phone_number="1",
            role=UserRole.CUSTOMER,
        )
    )
    test_db.commit()

    response = anon_client.post(
        "/token",
        data={"username": "auditee", "password": "Correct-Horse-9-Battery"},
    )
    assert response.status_code == 200

    events = [r for r in captured_audit() if r["event"] == "authentication"]
    successes = [r for r in events if r["outcome"] == "success"]

    assert successes, "a successful login left no record"
    assert successes[0]["actor"] == "auditee"
    # The issued token is the credential this route hands out; it must not
    # also be written to the trail.
    assert response.json()["access_token"] not in json.dumps(events)


def test_an_authorization_refusal_is_recorded(customer_client, captured_audit):
    """The useful part is which identity asked for what; the 403 alone does
    not say."""
    customer_client.get("/admin/stats/disk")

    events = [r for r in captured_audit() if r["event"] == "authorization"]

    assert events, "a denied request left no record"
    assert events[0]["outcome"] == "denied"


def test_a_privilege_change_is_recorded(chef_client, test_db, captured_audit):
    from db.models import User, UserRole

    from apis.auth.utils import get_password_hash

    test_db.add(
        User(
            id=98,
            username="promotee",
            password=get_password_hash("Correct-Horse-9-Battery"),
            first_name="A",
            last_name="B",
            phone_number="1",
            role=UserRole.CUSTOMER,
        )
    )
    test_db.commit()

    response = chef_client.put(
        "/users/update_role",
        json={"username": "promotee", "role": "Employee"},
    )
    assert response.status_code == 200

    events = [r for r in captured_audit() if r["event"] == "privilege_change"]

    assert events, "a role change left no record"
    assert events[0]["subject"] == "promotee"
    assert "role_set_to_Employee" == events[0]["action"]


def test_no_audit_record_anywhere_contains_a_password(
    chef_client, captured_audit
):
    """The broad sweep: whatever the routes above emitted, none of it may
    contain a credential."""
    chef_client.post(
        "/admin/reset-chef-password", json={"current_password": "not-the-password"}
    )

    serialized = json.dumps(captured_audit())

    assert "not-the-password" not in serialized


# --- what the trail deliberately omits ---------------------------------


def test_the_access_record_omits_the_query_string(anon_client, captured_audit):
    """A reset code or a token in the query string would otherwise be
    copied into the log verbatim."""
    anon_client.post("/token?reset_code=123456-secret", data={})

    serialized = json.dumps(captured_audit())

    assert "123456-secret" not in serialized
    assert "reset_code" not in serialized


def test_the_uvicorn_access_log_is_disabled():
    """It repeats the full request line including the query string, which is
    the one place the application's own records take care to omit."""
    configure_logging()

    assert logging.getLogger("uvicorn.access").disabled


def test_a_state_changing_request_is_recorded(employee_client, captured_audit):
    """The positive half of the selection rule. Without this, removing the
    middleware entirely still satisfies every other test here, because they
    all assert that something is *absent* from the trail."""
    employee_client.put(
        "/menu", json={"name": "Soup", "price": 9.5, "category": "Starters"}
    )

    http_events = [r for r in captured_audit() if r["event"] == "http_request"]

    assert http_events, "a state-changing request left no access record"
    assert http_events[0]["method"] == "PUT"
    assert http_events[0]["path"] == "/menu"
    assert http_events[0]["status_code"] == 201


def test_a_refused_request_is_recorded(customer_client, captured_audit):
    """A refusal is the event most worth having, and a GET that is refused
    would not be recorded by the state-changing rule alone."""
    customer_client.get("/admin/stats/disk")

    http_events = [r for r in captured_audit() if r["event"] == "http_request"]

    assert http_events, "a denied request left no access record"
    assert http_events[0]["outcome"] == "denied"
    assert http_events[0]["status_code"] == 403


def test_a_read_of_an_unremarkable_resource_is_not_recorded(
    anon_client, captured_audit
):
    """A trail that logs every menu read is one nobody reads."""
    anon_client.get("/menu")

    http_events = [r for r in captured_audit() if r["event"] == "http_request"]

    assert http_events == []
