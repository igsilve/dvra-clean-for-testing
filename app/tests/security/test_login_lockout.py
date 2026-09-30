"""T70 / T114: brute-force resistance on every authentication path.

Two layers are under test. The in-process throttle in apis.auth.utils.lockout
covers usernames that have no row in the database, and the persisted counter
on the user row survives a worker restart. The tests assert both, and assert
that a locked account is indistinguishable from a wrong password.
"""

from datetime import datetime, timedelta

import pytest
from apis.auth.utils import authenticate_user, get_password_hash
from apis.auth.utils.lockout import reset_all
from apis.auth.utils.utils import MAX_FAILED_LOGINS
from db.models import User, UserRole

PASSWORD = "C0rrect!Passw0rd"
WRONG = "Wr0ng!Passw0rd"


@pytest.fixture(autouse=True)
def clear_in_process_lockout():
    reset_all()
    yield
    reset_all()


def _make_user(test_db, username="lockme", user_id=400):
    user = User(
        id=user_id,
        username=username,
        password=get_password_hash(PASSWORD),
        first_name="Lock",
        last_name="Me",
        phone_number=f"555-0{user_id}",
        role=UserRole.CUSTOMER,
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.mark.security
def test_consecutive_failures_are_counted_and_persisted(test_db):
    user = _make_user(test_db)

    for expected in range(1, MAX_FAILED_LOGINS):
        assert authenticate_user(test_db, user.username, WRONG) is False
        test_db.refresh(user)
        assert user.failed_logins == expected
        assert user.locked_until is None


@pytest.mark.security
def test_account_stops_authenticating_once_the_threshold_is_reached(test_db):
    user = _make_user(test_db, user_id=401)

    for _ in range(MAX_FAILED_LOGINS):
        authenticate_user(test_db, user.username, WRONG)

    test_db.refresh(user)
    assert user.locked_until is not None

    # The correct password no longer works while the lock is in force.
    assert authenticate_user(test_db, user.username, PASSWORD) is False


@pytest.mark.security
def test_lock_expires_after_the_configured_window(test_db):
    user = _make_user(test_db, user_id=402)

    for _ in range(MAX_FAILED_LOGINS):
        authenticate_user(test_db, user.username, WRONG)

    test_db.refresh(user)
    user.locked_until = datetime.now() - timedelta(seconds=1)
    test_db.add(user)
    test_db.commit()

    assert authenticate_user(test_db, user.username, PASSWORD)


@pytest.mark.security
def test_successful_authentication_resets_the_counter(test_db):
    user = _make_user(test_db, user_id=403)

    for _ in range(MAX_FAILED_LOGINS - 1):
        authenticate_user(test_db, user.username, WRONG)
    test_db.refresh(user)
    assert user.failed_logins == MAX_FAILED_LOGINS - 1

    assert authenticate_user(test_db, user.username, PASSWORD)

    test_db.refresh(user)
    assert user.failed_logins == 0
    assert user.locked_until is None


@pytest.mark.security
def test_a_password_reset_clears_the_lock(test_db):
    """Otherwise five guesses would lock a user out of their own recovery."""
    from apis.auth.utils import update_user_password

    user = _make_user(test_db, user_id=404)
    for _ in range(MAX_FAILED_LOGINS):
        authenticate_user(test_db, user.username, WRONG)
    test_db.refresh(user)
    assert user.locked_until is not None

    update_user_password(test_db, user.username, "Brand!NewPassw0rd")

    test_db.refresh(user)
    assert user.failed_logins == 0
    assert user.locked_until is None


@pytest.mark.security
def test_locked_account_is_indistinguishable_from_a_wrong_password(
    test_db, anon_client
):
    """The response must not reveal that the lockout has engaged."""
    user = _make_user(test_db, user_id=405)

    wrong = anon_client.post(
        "/token", data={"username": user.username, "password": WRONG}
    )

    for _ in range(MAX_FAILED_LOGINS):
        authenticate_user(test_db, user.username, WRONG)
    test_db.refresh(user)
    assert user.locked_until is not None

    locked = anon_client.post(
        "/token", data={"username": user.username, "password": PASSWORD}
    )

    assert locked.status_code == wrong.status_code == 401
    assert locked.json() == wrong.json()
    assert "Retry-After" not in locked.headers


@pytest.mark.security
def test_unknown_usernames_are_throttled_too(test_db, anon_client):
    """A username with no row still has to be rate-limited somewhere.

    The persisted counter has nowhere to write for an account that does not
    exist, which is exactly why the in-process throttle is kept alongside it.
    """
    from apis.auth.utils.lockout import seconds_remaining

    for _ in range(MAX_FAILED_LOGINS):
        anon_client.post(
            "/token", data={"username": "ghost", "password": WRONG}
        )

    assert seconds_remaining("login", "ghost") > 0


@pytest.mark.security
def test_lockout_is_checked_before_the_password_is_verified(test_db, mocker):
    """A blocked attempt must not spend a hash comparison."""
    user = _make_user(test_db, user_id=406)
    user.locked_until = datetime.now() + timedelta(minutes=5)
    test_db.add(user)
    test_db.commit()

    spy = mocker.patch(
        "apis.auth.utils.utils.verify_and_upgrade_password",
        return_value=(True, None),
    )

    assert authenticate_user(test_db, user.username, PASSWORD) is False
    spy.assert_not_called()


@pytest.mark.security
def test_change_password_endpoint_throttles_guesses(test_db, anon_client):
    """A stolen token must not allow unlimited guessing of the current password."""
    from jwt_tokens import encode_token

    user = _make_user(test_db, username="tokenholder", user_id=407)
    headers = {
        "Authorization": f"Bearer {encode_token({'sub': user.username, 'ver': 0})}"
    }

    statuses = []
    for _ in range(MAX_FAILED_LOGINS + 1):
        response = anon_client.post(
            "/profile/password",
            headers=headers,
            json={"current_password": WRONG, "new_password": "An0ther!Passw0rd"},
        )
        statuses.append(response.status_code)

    assert statuses[-1] == 429, f"expected throttling, got {statuses}"
