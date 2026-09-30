"""Tests for the password hashing scheme and its cost parameters."""

from apis.auth.utils.utils import (
    authenticate_user,
    get_password_hash,
    pwd_context,
    verify_and_upgrade_password,
    verify_password,
)
from db.models import User, UserRole
from passlib.hash import bcrypt


def test_argon2id_is_the_preferred_scheme():
    """New hashes must use argon2id, with bcrypt kept only for verification."""
    assert pwd_context.schemes()[0] == "argon2"
    assert "bcrypt" in pwd_context.schemes()

    assert get_password_hash("password").startswith("$argon2id$")


def test_cost_parameters_are_set_explicitly():
    """Costs are pinned, so a passlib default change cannot weaken them."""
    configured = pwd_context.to_dict()
    assert configured["argon2__time_cost"] == 3
    assert configured["argon2__memory_cost"] == 65536
    assert configured["argon2__parallelism"] == 4
    assert configured["bcrypt__rounds"] == 12


def test_pinned_costs_are_encoded_in_the_produced_hash():
    """Stronger than reading config back: proves the costs actually applied."""
    assert "$m=65536,t=3,p=4$" in get_password_hash("password")


def test_existing_bcrypt_hashes_still_verify():
    legacy = bcrypt.using(rounds=12).hash("password")

    assert verify_password("password", legacy)
    assert not verify_password("wrong", legacy)


def test_legacy_bcrypt_hash_is_flagged_for_upgrade():
    legacy = bcrypt.using(rounds=12).hash("password")

    matched, new_hash = verify_and_upgrade_password("password", legacy)

    assert matched
    assert new_hash is not None
    assert new_hash.startswith("$argon2id$")


def test_a_current_argon2_hash_is_not_rehashed():
    current = get_password_hash("password")

    matched, new_hash = verify_and_upgrade_password("password", current)

    assert matched
    assert new_hash is None


def test_login_transparently_upgrades_a_legacy_hash(test_db):
    """The rehash must be persisted, not just computed."""
    legacy = bcrypt.using(rounds=12).hash("password")
    user = User(
        id=200,
        username="legacyhash",
        password=legacy,
        first_name="Legacy",
        last_name="",
        phone_number="7777",
        role=UserRole.CUSTOMER,
    )
    test_db.add(user)
    test_db.commit()

    assert authenticate_user(test_db, "legacyhash", "password")

    stored = test_db.query(User).filter(User.username == "legacyhash").first()
    assert stored.password.startswith("$argon2id$")
    assert stored.password != legacy

    # The migrated hash must still authenticate on the next login.
    assert authenticate_user(test_db, "legacyhash", "password")
    assert not authenticate_user(test_db, "legacyhash", "wrong")


def test_failed_login_does_not_rewrite_the_stored_hash(test_db):
    legacy = bcrypt.using(rounds=12).hash("password")
    user = User(
        id=201,
        username="legacyhash2",
        password=legacy,
        first_name="Legacy",
        last_name="",
        phone_number="7778",
        role=UserRole.CUSTOMER,
    )
    test_db.add(user)
    test_db.commit()

    assert not authenticate_user(test_db, "legacyhash2", "wrong")

    stored = test_db.query(User).filter(User.username == "legacyhash2").first()
    assert stored.password == legacy
