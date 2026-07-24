import hashlib
import secrets
from datetime import datetime, timedelta

from db.models import User
from sqlalchemy.orm import Session

from .utils import send_code_to_phone_number


def _hash_reset_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def generate_and_send_code_to_user(user: User, db: Session):
    raw_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    user.reset_password_code = _hash_reset_code(raw_code)
    user.reset_password_code_expiry_date = datetime.now() + timedelta(minutes=15)
    db.add(user)
    db.commit()

    success = send_code_to_phone_number(user.phone_number, raw_code)
    return success
