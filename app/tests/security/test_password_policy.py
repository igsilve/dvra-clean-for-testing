"""T69 / T230: one password policy, applied to users and system accounts alike.

The point of these tests is parity. It is easy to tighten the rule for
customers and leave service credentials on whatever the config file happened
to contain, so the checks below assert that both paths reach the same
validator and that a system account cannot be created or used with a
credential a customer would be refused.
"""

import pytest
from apis.auth.schemas import NewPasswordData, UserCreate
from db.models import User, UserRole
from password_policy import (
    MIN_LENGTH,
    PasswordPolicyError,
    validate_password_policy,
    validate_system_account_password,
)
from pydantic import ValidationError

WEAK_PASSWORDS = (
    "",
    "short",
    "password",
    "12345678",
    "kaylee123",
    "th4tsmyp4ssw0rd!",
    "alllowercase1!",
    "ALLUPPERCASE1!",
    "NoDigitsHere!!",
    "NoSymbols12345",
)

STRONG_PASSWORD = "Str0ng!Passw0rd123"


@pytest.mark.security
@pytest.mark.parametrize("password", WEAK_PASSWORDS)
def test_weak_passwords_are_rejected_for_end_users(password):
    with pytest.raises(PasswordPolicyError):
        validate_password_policy(password)


@pytest.mark.security
@pytest.mark.parametrize("password", WEAK_PASSWORDS)
def test_weak_passwords_are_rejected_for_system_accounts(password):
    """The parity assertion: no weaker baseline for machine credentials."""
    with pytest.raises(PasswordPolicyError):
        validate_system_account_password(password, subject="TEST_CREDENTIAL")


@pytest.mark.security
def test_system_and_user_validators_agree_on_every_case():
    candidates = list(WEAK_PASSWORDS) + [STRONG_PASSWORD, "An0ther!Passw0rd"]

    for password in candidates:
        user_ok = _accepts(validate_password_policy, password)
        system_ok = _accepts(
            lambda value: validate_system_account_password(value, subject="x"),
            password,
        )
        assert user_ok == system_ok, f"policy diverged for {password!r}"


def _accepts(validator, password):
    try:
        validator(password)
        return True
    except PasswordPolicyError:
        return False


@pytest.mark.security
def test_strong_password_is_accepted_and_returned_unchanged():
    assert validate_password_policy(STRONG_PASSWORD) == STRONG_PASSWORD
    assert (
        validate_system_account_password(STRONG_PASSWORD, subject="x")
        == STRONG_PASSWORD
    )


@pytest.mark.security
def test_policy_error_never_discloses_the_credential():
    """A bootstrap failure is logged; it must not carry the value with it."""
    try:
        validate_system_account_password(
            "kaylee123", subject="POSTGRES_PASSWORD"
        )
    except PasswordPolicyError as exc:
        assert "kaylee123" not in str(exc)
        assert "POSTGRES_PASSWORD" in str(exc)
    else:
        pytest.fail("expected the weak credential to be rejected")


@pytest.mark.security
def test_minimum_length_is_at_least_twelve():
    assert MIN_LENGTH >= 12


@pytest.mark.security
def test_registration_schema_rejects_a_weak_password():
    with pytest.raises(ValidationError):
        UserCreate(
            username="someone",
            password="password",
            phone_number="555-0100",
        )


@pytest.mark.security
def test_registration_schema_accepts_a_compliant_password():
    user = UserCreate(
        username="someone",
        password=STRONG_PASSWORD,
        phone_number="555-0100",
    )
    assert user.password == STRONG_PASSWORD


@pytest.mark.security
def test_reset_schema_rejects_a_weak_new_password():
    with pytest.raises(ValidationError):
        NewPasswordData(
            username="someone",
            reset_password_code="1234",
            new_password="12345678",
        )


@pytest.mark.security
def test_register_endpoint_rejects_a_weak_password(test_db, anon_client):
    response = anon_client.post(
        "/register",
        json={
            "username": "weakling",
            "password": "password",
            "first_name": "Weak",
            "last_name": "Ling",
            "phone_number": "555-0199",
        },
    )

    assert response.status_code == 422
    assert test_db.query(User).filter(User.username == "weakling").first() is None


@pytest.mark.security
def test_generated_seed_passwords_satisfy_the_policy():
    """The seeding generator is held to the policy it enforces on others."""
    from init import generate_random_secret

    for _ in range(50):
        validate_password_policy(generate_random_secret())


@pytest.mark.security
def test_database_credential_is_validated_before_a_connection_is_made(monkeypatch):
    """A weak POSTGRES_PASSWORD must stop start-up, not reach the server."""
    from config import settings
    from db import session as session_module

    # DATABASE_URL is a computed property, so it is replaced on the class.
    monkeypatch.setattr(
        type(settings),
        "DATABASE_URL",
        property(lambda self: "postgresql://u:p@localhost:5432/db"),
    )
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", "password", raising=False)

    connected = False

    def _fail_if_called(*args, **kwargs):
        nonlocal connected
        connected = True
        raise AssertionError("engine was created despite a weak credential")

    monkeypatch.setattr(session_module, "create_engine", _fail_if_called)

    with pytest.raises(PasswordPolicyError):
        session_module._create_engine_and_session()

    assert connected is False


@pytest.mark.security
def test_seeded_accounts_are_flagged_to_force_a_password_change(test_db):
    from init import load_demo_users, load_users

    load_users(test_db)
    load_demo_users(test_db)

    seeded = test_db.query(User).all()
    assert seeded, "expected the seeding routine to create accounts"
    for user in seeded:
        assert user.must_change_password is True, (
            f"{user.username} was seeded with a system-issued password but is "
            "not required to change it"
        )


def _seed_flagged_chef(test_db, password=STRONG_PASSWORD):
    from apis.auth.utils import get_password_hash

    user = User(
        id=320,
        username="freshchef",
        password=get_password_hash(password),
        first_name="Fresh",
        last_name="Chef",
        phone_number="555-0300",
        role=UserRole.CHEF,
        must_change_password=True,
    )
    test_db.add(user)
    test_db.commit()
    return user


def _auth_header(user):
    """Mint a real token.

    The shared client fixtures override get_current_user outright, which
    would step over the very check under test, so these cases go through
    the genuine dependency chain.
    """
    from jwt_tokens import encode_token

    token = encode_token({"sub": user.username, "ver": user.token_version or 0})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.security
def test_flagged_account_cannot_use_the_application(test_db, anon_client):
    user = _seed_flagged_chef(test_db)

    response = anon_client.get("/profile", headers=_auth_header(user))

    assert response.status_code == 403
    assert "Password change required" in response.json()["detail"]


@pytest.mark.security
def test_flagged_account_can_change_its_own_password_and_is_then_usable(
    test_db, anon_client
):
    """The flag has to be escapable, or the seeded chef is bricked.

    The code-by-phone reset is customer-only, so this endpoint is the only
    recovery path staff and the chef have.
    """
    user = _seed_flagged_chef(test_db)
    replacement = "Repl4cement!Pass"

    response = anon_client.post(
        "/profile/password",
        headers=_auth_header(user),
        json={"current_password": STRONG_PASSWORD, "new_password": replacement},
    )
    assert response.status_code == 200

    test_db.refresh(user)
    assert user.must_change_password is False

    # The old token died with the password change; a fresh one works.
    assert anon_client.get("/profile", headers=_auth_header(user)).status_code == 200


@pytest.mark.security
def test_change_password_requires_the_current_password(test_db, anon_client):
    user = _seed_flagged_chef(test_db)

    response = anon_client.post(
        "/profile/password",
        headers=_auth_header(user),
        json={"current_password": "WrongPassw0rd!", "new_password": "Repl4cement!Pass"},
    )

    assert response.status_code == 400
    test_db.refresh(user)
    assert user.must_change_password is True


@pytest.mark.security
def test_change_password_enforces_the_shared_policy(test_db, anon_client):
    user = _seed_flagged_chef(test_db)

    response = anon_client.post(
        "/profile/password",
        headers=_auth_header(user),
        json={"current_password": STRONG_PASSWORD, "new_password": "password"},
    )

    assert response.status_code == 422
    test_db.refresh(user)
    assert user.must_change_password is True
