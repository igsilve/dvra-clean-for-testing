import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Union

from apis.auth.exceptions import UserAlreadyExistsException
from config import Settings
from db.models import User, UserRole
from jose import jwt
from passlib.context import CryptContext
from utils.pseudonymize import pseudonymize

_audit = logging.getLogger("audit.auth")

SECRET_KEY = Settings.JWT_SECRET_KEY
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_LOCKOUT_THRESHOLD = 5
_LOCKOUT_DURATION_SECONDS = 300  # 5 minutes
_auth_failure_state: dict[str, dict] = {}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user_by_username(db, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    return user


def get_user_by_id(db, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    return user


def update_user_password(db, username: str, password: str) -> User:
    db_user = get_user_by_username(db, username)
    db_user.password = get_password_hash(password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_user_by_phone_number(db, phone_number: str) -> User:
    user = db.query(User).filter(User.phone_number == pseudonymize(phone_number)).first()
    return user


def _is_locked_out(username: str) -> bool:
    state = _auth_failure_state.get(username)
    if not state:
        return False
    if state["count"] >= _LOCKOUT_THRESHOLD:
        if time.monotonic() - state["since"] < _LOCKOUT_DURATION_SECONDS:
            return True
        del _auth_failure_state[username]
    return False


def _record_failure(username: str) -> None:
    state = _auth_failure_state.get(username)
    if state and time.monotonic() - state["since"] < _LOCKOUT_DURATION_SECONDS:
        state["count"] += 1
    else:
        _auth_failure_state[username] = {"count": 1, "since": time.monotonic()}


def _reset_failures(username: str) -> None:
    _auth_failure_state.pop(username, None)


def authenticate_user(db, username: str, password: str, client_ip: str = "unknown"):
    if _is_locked_out(username):
        _audit.warning("auth_locked_out username=%s ip=%s", username, client_ip)
        return False
    user = get_user_by_username(db, username)
    if not user:
        _record_failure(username)
        _audit.warning("auth_failed reason=unknown_user username=%s ip=%s", username, client_ip)
        return False
    if not verify_password(password, user.password):
        _record_failure(username)
        _audit.warning("auth_failed reason=wrong_password username=%s ip=%s", username, client_ip)
        return False
    _audit.info("auth_success username=%s ip=%s", username, client_ip)
    _reset_failures(username)
    return user


def create_user(
    db,
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    phone_number: str,
    role: str = UserRole.CUSTOMER,
):
    if get_user_by_phone_number(db, phone_number) or get_user_by_username(db, username):
        raise UserAlreadyExistsException()

    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        phone_number=pseudonymize(phone_number),
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def create_user_if_not_exists(
    db,
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    phone_number: str,
    role: str = UserRole.CUSTOMER,
):
    try:
        return create_user(
            db, username, password, first_name, last_name, phone_number, role
        )
    except UserAlreadyExistsException:
        return None


def update_user(db, username: str, user):
    db_user = get_user_by_username(db, username)

    for var, value in vars(user).items():
        if value:
            setattr(db_user, var, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    import secrets as _secrets
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    # jti provides a unique token ID preventing token reuse/fixation
    to_encode.update({"exp": expire, "jti": _secrets.token_hex(16)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


import os as _os
import time as _time

_SMS_SEND_WINDOW = 3600  # 1 hour
_SMS_SEND_LIMIT = 3
_sms_send_state: dict[str, dict] = {}


def _check_sms_rate_limit(phone_number: str) -> None:
    now = _time.monotonic()
    state = _sms_send_state.get(phone_number)
    if state and now - state["since"] < _SMS_SEND_WINDOW:
        if state["count"] >= _SMS_SEND_LIMIT:
            raise RuntimeError("SMS rate limit exceeded — try again later")
        state["count"] += 1
    else:
        _sms_send_state[phone_number] = {"count": 1, "since": now}


def send_code_to_phone_number(phone_number: str, code: str) -> bool:
    _check_sms_rate_limit(phone_number)
    sms_gateway_url = _os.getenv("SMS_GATEWAY_URL")
    sms_api_key = _os.getenv("SMS_API_KEY")
    sms_from = _os.getenv("SMS_FROM_NUMBER")
    if sms_gateway_url and sms_api_key and sms_from:
        import requests as _req
        response = _req.post(
            sms_gateway_url,
            auth=(sms_api_key, ""),
            data={"To": phone_number, "From": sms_from, "Body": f"Your verification code: {code}"},
            timeout=10,
        )
        response.raise_for_status()
        _audit.info("sms_sent phone_hash=%s", hashlib.sha256(phone_number.encode()).hexdigest()[:12])
    else:
        _audit.warning("sms_gateway_not_configured phone_hash=%s", hashlib.sha256(phone_number.encode()).hexdigest()[:12])
    return True
