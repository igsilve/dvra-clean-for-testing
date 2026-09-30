"""One password policy, applied to every kind of account.

Server-to-server credentials are the ones most often given a weaker rule than
end users get, on the reasoning that they live in a secret store and are
therefore "trusted". They are not: a weak service password reaches production
just as silently, and it typically guards more than a single user's data.

This module is the only place the baseline is defined. Callers may add
stricter requirements on top; nothing may relax it.
"""

import string
from typing import Iterable

MIN_LENGTH = 12

# Credentials that must never be accepted regardless of length or composition,
# including the values this project previously shipped as defaults.
FORBIDDEN_PASSWORDS = frozenset(
    {
        "password",
        "password1",
        "password123",
        "password456",
        "passw0rd",
        "12345678",
        "123456789",
        "1234567890",
        "qwerty",
        "letmein",
        "changeme",
        "admin",
        "administrator",
        "secret",
        "kaylee123",
        "th4tsmyp4ssw0rd!",
    }
)

_SYMBOLS = set(string.punctuation)


class PasswordPolicyError(ValueError):
    """Raised when a password does not meet the shared baseline."""


def describe_policy() -> str:
    return (
        f"Passwords must be at least {MIN_LENGTH} characters and include "
        "lower-case and upper-case letters, a digit and a symbol."
    )


def _missing_character_classes(password: str) -> Iterable[str]:
    if not any(char.islower() for char in password):
        yield "a lower-case letter"
    if not any(char.isupper() for char in password):
        yield "an upper-case letter"
    if not any(char.isdigit() for char in password):
        yield "a digit"
    if not any(char in _SYMBOLS for char in password):
        yield "a symbol"


def validate_password_policy(password: str, *, subject: str = "password") -> str:
    """Return the password unchanged, or raise PasswordPolicyError.

    `subject` names what is being validated so a bootstrap failure says which
    credential is at fault without ever including the value itself.
    """
    if not isinstance(password, str) or not password:
        raise PasswordPolicyError(f"{subject} must be provided")

    if len(password) < MIN_LENGTH:
        raise PasswordPolicyError(
            f"{subject} must be at least {MIN_LENGTH} characters"
        )

    if password.lower() in FORBIDDEN_PASSWORDS:
        raise PasswordPolicyError(f"{subject} is a commonly used password")

    missing = list(_missing_character_classes(password))
    if missing:
        raise PasswordPolicyError(f"{subject} must include {', '.join(missing)}")

    return password


def validate_system_account_password(password: str, *, subject: str) -> str:
    """Validate a server-to-server credential.

    Delegates to the shared baseline rather than applying its own rules, so a
    system account can never end up held to a weaker standard than a
    customer's. Extra requirements may be added here, never removals.
    """
    return validate_password_policy(password, subject=subject)
