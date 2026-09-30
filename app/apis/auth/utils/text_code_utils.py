import hmac
import secrets
from datetime import datetime, timedelta
from hashlib import sha256

from config import settings
from db.models import User
from sqlalchemy.orm import Session

from .utils import send_code_to_phone_number

# Eight digits rather than four. Bounding the guesses against a single code
# is not enough on its own, because a caller can keep requesting new codes
# and spend a fresh budget against each one; widening the space is what
# makes that grind uneconomic.
RESET_CODE_DIGITS = 8

# Short enough that a code intercepted from an SMS has little time to be
# used, long enough for someone to read it off a phone and type it.
RESET_CODE_LIFETIME = timedelta(minutes=10)


def hash_reset_code(code: str) -> str:
    """Derive the stored form of a reset code.

    The code is never written to the database as sent. A reset code is a
    password for the duration of its life, and anyone with read access to
    the users table — a backup, a log of a query, an injection elsewhere —
    could otherwise complete a reset for any account without knowing
    anything about it.

    Keyed rather than a bare digest: eight digits is a space small enough
    to precompute exhaustively, so an unkeyed hash would not slow an
    attacker holding the table down at all.
    """
    return hmac.new(
        settings.OTP_HMAC_KEY.encode(), code.encode(), sha256
    ).hexdigest()


def reset_code_matches(user: User, submitted_code: str) -> bool:
    """Constant-time comparison against the stored derivation."""
    if not user.reset_password_code:
        return False

    return hmac.compare_digest(
        user.reset_password_code, hash_reset_code(submitted_code)
    )


def generate_and_send_code_to_user(user: User, db: Session):
    code = "".join(str(secrets.randbelow(10)) for _ in range(RESET_CODE_DIGITS))

    user.reset_password_code = hash_reset_code(code)
    user.reset_password_code_expiry_date = datetime.now() + RESET_CODE_LIFETIME
    # A new code starts with a full attempt budget; otherwise a user who
    # mistyped the previous one would find the replacement already spent.
    user.reset_password_attempts = 0
    db.add(user)
    db.commit()

    # The recipient gets the code itself; only the derivation is retained.
    success = send_code_to_phone_number(user.phone_number, code)
    return success
