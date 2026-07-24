import secrets
import string

from db.models import User
from sqlalchemy.orm import Session

_REFERRAL_ALPHABET = string.ascii_uppercase + string.digits


def _generate_code() -> str:
    return "".join(secrets.choice(_REFERRAL_ALPHABET) for _ in range(8))


def get_referral_code(db: Session, db_user: User) -> str:
    """Get or generate a referral code for the user."""
    if db_user.referral_code is None:
        db_user.referral_code = _generate_code()
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    return db_user.referral_code
