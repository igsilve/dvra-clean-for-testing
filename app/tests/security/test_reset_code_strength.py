"""T78: the password reset code must not be guessable.

The window is ten minutes, so the only things standing between an
attacker and an account takeover are the size of the code space and the
number of guesses allowed against it. Both are asserted here.
"""

from datetime import datetime, timedelta

import pytest
from apis.auth.services.reset_password_new_password_service import MAX_CODE_ATTEMPTS
from apis.auth.utils import get_password_hash
from apis.auth.utils.lockout import reset_all
from apis.auth.utils.text_code_utils import RESET_CODE_DIGITS, hash_reset_code
from db.models import User, UserRole

CODE = "13579024"
NEW_PASSWORD = "Res3t!Passw0rd"


@pytest.fixture(autouse=True)
def clear_in_process_lockout():
    reset_all()
    yield
    reset_all()


def _user_with_code(test_db, user_id=600, code=CODE):
    user = User(
        id=user_id,
        username=f"resetme{user_id}",
        password=get_password_hash("Or1ginal!Passw0rd"),
        first_name="Reset",
        last_name="Me",
        phone_number=f"555-2{user_id}",
        role=UserRole.CUSTOMER,
        # Stored the way the issuer stores it: a keyed derivation, never
        # the code as sent.
        reset_password_code=hash_reset_code(code) if code else None,
        reset_password_code_expiry_date=datetime.now() + timedelta(minutes=15),
    )
    test_db.add(user)
    test_db.commit()
    return user


def _guess(client, user, code):
    return client.post(
        "/reset-password/new-password",
        json={
            "username": user.username,
            "reset_password_code": code,
            "new_password": NEW_PASSWORD,
        },
    )


@pytest.mark.security
def test_the_code_space_is_wide_enough_to_resist_grinding():
    """Four digits is 10,000 codes; a fresh code per request grinds that down."""
    assert RESET_CODE_DIGITS >= 8


@pytest.mark.security
def test_issued_codes_use_the_full_width(test_db, monkeypatch):
    from apis.auth.utils import text_code_utils

    user = _user_with_code(test_db, user_id=601, code=None)

    # The code is only ever seen by the recipient, so it is captured at
    # the point of delivery rather than read back out of the database.
    sent = []
    monkeypatch.setattr(
        text_code_utils,
        "send_code_to_phone_number",
        lambda number, code: sent.append(code) or True,
    )

    for _ in range(25):
        text_code_utils.generate_and_send_code_to_user(user, test_db)
        assert len(sent[-1]) == RESET_CODE_DIGITS
        assert sent[-1].isdigit()

    assert len(set(sent)) > 20, "issued codes are not sufficiently unpredictable"


@pytest.mark.security
def test_the_code_is_not_stored_as_sent(test_db, monkeypatch):
    """Read access to the users table must not hand over a working code.

    A reset code is a password for as long as it lives. Stored plainly, a
    backup or a stray query log lets someone complete a reset for any
    account without knowing anything about it.
    """
    from apis.auth.utils import text_code_utils

    user = _user_with_code(test_db, user_id=608, code=None)

    sent = []
    monkeypatch.setattr(
        text_code_utils,
        "send_code_to_phone_number",
        lambda number, code: sent.append(code) or True,
    )
    text_code_utils.generate_and_send_code_to_user(user, test_db)

    test_db.refresh(user)
    assert user.reset_password_code != sent[0]
    assert sent[0] not in user.reset_password_code


@pytest.mark.security
def test_the_stored_derivation_is_keyed(test_db, monkeypatch):
    """An unkeyed digest of eight digits is precomputable end to end."""
    from apis.auth.utils import text_code_utils
    from config import settings

    baseline = text_code_utils.hash_reset_code("13579024")

    monkeypatch.setattr(
        type(settings), "OTP_HMAC_KEY", property(lambda self: "a-different-key")
    )

    assert text_code_utils.hash_reset_code("13579024") != baseline, (
        "the stored value does not depend on a server-side key, so an "
        "attacker holding the table can build a lookup for every code"
    )


@pytest.mark.security
def test_code_is_destroyed_after_a_bounded_number_of_failed_attempts(
    test_db, anon_client
):
    user = _user_with_code(test_db, user_id=602)

    for _ in range(MAX_CODE_ATTEMPTS):
        assert _guess(anon_client, user, "00000000").status_code == 400

    test_db.refresh(user)
    assert user.reset_password_code is None

    # Even the correct code is now useless: the attacker cannot outlast the
    # bound by waiting for either throttle to lapse. Both are cleared here so
    # the refusal below can only come from the code being destroyed.
    from rate_limiting import limiter

    reset_all()
    limiter.reset()
    assert _guess(anon_client, user, CODE).status_code == 400


@pytest.mark.security
def test_failed_attempts_are_persisted_on_the_account(test_db, anon_client):
    user = _user_with_code(test_db, user_id=603)

    _guess(anon_client, user, "00000000")

    test_db.refresh(user)
    assert user.reset_password_attempts == 1


@pytest.mark.security
def test_a_new_code_restores_the_attempt_budget(test_db, anon_client):
    """A user who mistyped must not find the replacement code already spent."""
    from apis.auth.utils.text_code_utils import generate_and_send_code_to_user

    user = _user_with_code(test_db, user_id=604)
    _guess(anon_client, user, "00000000")
    test_db.refresh(user)
    assert user.reset_password_attempts == 1

    generate_and_send_code_to_user(user, test_db)

    test_db.refresh(user)
    assert user.reset_password_attempts == 0


@pytest.mark.security
def test_a_successful_reset_clears_the_counter(test_db, anon_client):
    user = _user_with_code(test_db, user_id=605)
    _guess(anon_client, user, "00000000")

    assert _guess(anon_client, user, CODE).status_code == 200

    test_db.refresh(user)
    assert user.reset_password_attempts == 0
    assert user.reset_password_code is None


@pytest.mark.security
def test_failures_are_indistinguishable(test_db, anon_client):
    """An unknown user, a wrong code and an expired code must look alike."""
    user = _user_with_code(test_db, user_id=606)

    wrong_code = _guess(anon_client, user, "00000000")

    expired = _user_with_code(test_db, user_id=607)
    expired.reset_password_code_expiry_date = datetime.now() - timedelta(minutes=1)
    test_db.add(expired)
    test_db.commit()
    expired_response = _guess(anon_client, expired, CODE)

    class _Ghost:
        username = "nobody-at-all"

    unknown = _guess(anon_client, _Ghost(), CODE)

    assert wrong_code.status_code == expired_response.status_code == 400
    assert unknown.status_code == 400
    assert wrong_code.json() == expired_response.json() == unknown.json()


@pytest.mark.security
def test_the_endpoint_is_rate_limited_per_source(test_db, anon_client):
    """Per-account bounds do not stop spraying many accounts from one host."""
    statuses = []
    for index in range(8):
        user = _user_with_code(test_db, user_id=610 + index)
        statuses.append(_guess(anon_client, user, "00000000").status_code)

    assert 429 in statuses, f"expected a per-source limit, got {statuses}"


@pytest.mark.security
def test_comparison_of_the_code_is_constant_time():
    """A short-circuiting compare leaks the code one digit at a time."""
    import inspect

    from apis.auth.services import reset_password_new_password_service as module

    from apis.auth.utils import text_code_utils

    comparison = inspect.getsource(text_code_utils)
    assert "hmac.compare_digest(" in comparison

    for source in (inspect.getsource(module), comparison):
        assert "user.reset_password_code ==" not in source
        assert "user.reset_password_code !=" not in source
