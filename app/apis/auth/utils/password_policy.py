import re


_MIN_LENGTH = 8
_POLICY_DESCRIPTION = (
    "Password must be at least 8 characters and contain uppercase, lowercase, "
    "digit, and special character."
)


def validate_password_policy(password: str) -> bool:
    if len(password) < _MIN_LENGTH:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


def require_password_policy(password: str, label: str = "Password") -> None:
    if not validate_password_policy(password):
        raise ValueError(f"{label}: {_POLICY_DESCRIPTION}")
