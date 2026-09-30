from datetime import datetime, timedelta, timezone
from typing import Union

from apis.auth.exceptions import UserAlreadyExistsException
from config import Settings
from db.models import User, UserRole
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = Settings.JWT_SECRET_KEY
ALGORITHM = "HS256"

# argon2 is listed first, so it is the scheme used for every new hash;
# passlib's argon2 handler is argon2id. bcrypt stays in the list for
# verification only, which is what lets existing hashes keep working.
# Cost parameters are pinned rather than left to library defaults so that a
# passlib upgrade cannot silently weaken them: time_cost=3 with 64 MiB of
# memory and 4 lanes follows the OWASP argon2id guidance, and bcrypt work
# factor 12 is the floor for the hashes being retired.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def verify_and_upgrade_password(plain_password: str, hashed_password: str):
    """Verify a password and return a replacement hash when one is due.

    Returns `(matched, new_hash)`. `new_hash` is not None only when the stored
    hash used a deprecated scheme or weaker parameters, which is the only
    moment the plaintext is available to rehash with.
    """
    return pwd_context.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
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
    user = db.query(User).filter(User.phone_number == phone_number).first()
    return user


def authenticate_user(db, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False

    matched, new_hash = verify_and_upgrade_password(password, user.password)
    if not matched:
        return False

    # A successful login is the only point where the plaintext exists, so it
    # is the only chance to migrate a legacy bcrypt hash to argon2id.
    if new_hash:
        user.password = new_hash
        db.add(user)
        db.commit()
        db.refresh(user)

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
        phone_number=phone_number,
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
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def send_code_to_phone_number(phone_number: str, code: str):
    # normally this would send a code to the phone number using
    # a third party service
    print(f"Sending code {code} to phone number {phone_number}")
    return True
