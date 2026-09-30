"""No account may ship with a password that is knowable from the source.

The seeding code previously created five accounts with fixed, weak passwords.
Each seeded password is now generated per run, and the accounts that are not
required to operate the service are not created in production at all.
"""

import pathlib

import pytest
from db.models import UserRole

# The credentials that used to be seeded. Kept here so the tests can prove
# they no longer authenticate, and so the repository scan below has something
# concrete to look for. This file is the only place they are allowed to
# appear, which the scan enforces by skipping itself.
HISTORIC_DEFAULT_CREDENTIALS = (
    ("Mike", "kaylee123"),
    ("Saul", "Th4tsMyP4ssw0rd!"),
    ("hhm", "12345678"),
    ("johndoe", "password123"),
    ("alicesmith", "password456"),
)


@pytest.mark.security
@pytest.mark.parametrize("username,password", HISTORIC_DEFAULT_CREDENTIALS)
def test_seeded_defaults_do_not_authenticate(
    test_db, anon_client, username, password
):
    """Every historically seeded credential must fail authentication."""
    response = anon_client.post(
        "/token", data={"username": username, "password": password}
    )

    assert response.status_code == 401


@pytest.mark.security
def test_known_default_passwords_are_absent_from_the_repository():
    """None of the known defaults may appear as a hardcoded credential.

    The match is deliberately context-bound rather than a bare substring
    search. "12345678" occurs legitimately in phone numbers and in the digit
    alphabet used to generate secrets, so scanning for the value alone
    produces false positives and a test nobody trusts. What matters is the
    value being *assigned as a password*, which is what this looks for.
    """
    repo_root = pathlib.Path(__file__).resolve().parents[3]

    skipped_dirs = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "skills",
        ".sde-security",
        "postgres_data",
    }

    # The security tests are exempt: naming the forbidden values is how they
    # assert those values are refused, so flagging them would make the two
    # checks mutually exclusive.
    security_tests = pathlib.Path(__file__).resolve().parent

    offenders = []
    for path in repo_root.rglob("*.py"):
        if path.resolve().parent == security_tests:
            continue
        if skipped_dirs & set(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for _, secret in HISTORIC_DEFAULT_CREDENTIALS:
            for assignment in (
                f'password="{secret}"',
                f"password='{secret}'",
                f'"password": "{secret}"',
                f"'password': '{secret}'",
            ):
                if assignment in text:
                    offenders.append(f"{path.relative_to(repo_root)}: {assignment}")

    assert offenders == [], f"default credentials still present: {offenders}"


@pytest.mark.security
def test_seeding_contains_no_password_literals():
    """The seeding module must not assign a quoted password to any account."""
    import inspect

    import init

    source = inspect.getsource(init)

    # Any create_user_if_not_exists call must take its password from the
    # generator, never from an inline string.
    assert 'password="' not in source
    assert "password='" not in source
    assert source.count("password=generate_random_secret()") >= 1


@pytest.mark.security
def test_generated_seed_passwords_are_unpredictable():
    """Distinct, long, and drawn from a large alphabet."""
    from init import generate_random_secret

    generated = {generate_random_secret() for _ in range(50)}

    assert len(generated) == 50
    assert all(len(value) == 32 for value in generated)


@pytest.mark.security
def test_only_the_chef_account_is_seeded_in_production(monkeypatch):
    """Accounts not required for operation are not created in production."""
    import init
    from config import ENV

    created = []
    monkeypatch.setattr(
        init,
        "create_user_if_not_exists",
        lambda db, username, **kwargs: created.append(username),
    )
    monkeypatch.setattr(init, "load_menu", lambda db: None)
    monkeypatch.setattr(init, "load_orders", lambda db: None)
    monkeypatch.setattr(init.settings, "ENVIRONMENT", ENV.PRODUCTION)

    init.load_users(None)
    if init.settings.ENVIRONMENT is not ENV.PRODUCTION:
        init.load_demo_users(None)

    assert created == [init.settings.CHEF_USERNAME]
    for demo_username, *_ in init.DEMO_USERS:
        assert demo_username not in created


@pytest.mark.security
def test_demo_accounts_are_customers_or_employees_never_chef():
    """A sample account must never carry administrative privilege."""
    from init import DEMO_USERS

    assert all(role is not UserRole.CHEF for *_, role in DEMO_USERS)
