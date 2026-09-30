import secrets
import string

from db.models import User
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

ALPHABET = string.ascii_uppercase + string.digits

# 36**13 is about 2**67. The previous eight characters gave roughly 41 bits,
# which is enumerable: a referral code is a bearer credential for whatever
# the referral is worth, and nothing rate-limits guessing a code that
# happens to exist.
CODE_LENGTH = 13

# Two independent codes colliding at this size is vanishingly unlikely, so
# the retry exists for the case that actually happens: a concurrent request
# taking the same code between our generation and our commit.
MAX_ATTEMPTS = 5


def _generate_code() -> str:
    """Generate a referral code from the cryptographic random source.

    `random` draws from a Mersenne Twister, whose state is recoverable from
    a few hundred outputs, so codes issued after that are predictable
    rather than merely guessable.
    """
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def get_referral_code(db: Session, db_user: User) -> str:
    """Get or generate a referral code for the user."""
    if db_user.referral_code is not None:
        return db_user.referral_code

    for _ in range(MAX_ATTEMPTS):
        db_user.referral_code = _generate_code()
        db.add(db_user)
        try:
            db.commit()
        except IntegrityError:
            # The unique constraint is the authority on whether the code is
            # taken; checking with a SELECT first would leave a window.
            db.rollback()
            continue
        db.refresh(db_user)
        return db_user.referral_code

    raise HTTPException(
        status_code=503, detail="Could not allocate a referral code"
    )
