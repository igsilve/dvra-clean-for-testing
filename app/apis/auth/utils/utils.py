from datetime import datetime, timedelta
from typing import Union

from apis.auth.exceptions import UserAlreadyExistsException
from db.models import User, UserRole
from jwt_tokens import encode_token, invalidate_issued_tokens
from passlib.context import CryptContext

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

# The only columns a caller may change through `update_user`. Deliberately
# excludes username, which identifies the account rather than describing it,
# and role, password and token_version, which are privilege.
UPDATABLE_PROFILE_FIELDS = frozenset({"first_name", "last_name", "phone_number"})


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
    # Every password change revokes the tokens issued under the old one, so
    # an attacker holding a stolen token loses access the moment the victim
    # resets. This is the choke point for both the self-service reset and the
    # administrative chef reset.
    invalidate_issued_tokens(db_user)
    # The holder has now chosen their own password, so whatever the system
    # issued at seeding time no longer gates the account.
    db_user.must_change_password = False
    # Clear the lock too. Otherwise an attacker could lock an account out of
    # its own recovery by spending five guesses, turning the control into a
    # denial of service.
    db_user.failed_logins = 0
    db_user.locked_until = None
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_user_by_phone_number(db, phone_number: str) -> User:
    user = db.query(User).filter(User.phone_number == phone_number).first()
    return user


MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


def authenticate_user(db, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False

    # Lockout is checked before the password is verified. Verifying first
    # would still run an argon2 hash on every blocked attempt, which both
    # wastes the CPU the lockout was meant to protect and makes a locked
    # account distinguishable by response time.
    if user.locked_until and user.locked_until > datetime.now():
        return False

    matched, new_hash = verify_and_upgrade_password(password, user.password)
    if not matched:
        user.failed_logins = (user.failed_logins or 0) + 1
        if user.failed_logins >= MAX_FAILED_LOGINS:
            user.locked_until = datetime.now() + LOCKOUT_WINDOW
        db.add(user)
        db.commit()
        return False

    if user.failed_logins or user.locked_until:
        user.failed_logins = 0
        user.locked_until = None
        db.add(user)
        db.commit()

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
    must_change_password: bool = False,
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
        must_change_password=must_change_password,
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
    must_change_password: bool = False,
):
    try:
        return create_user(
            db,
            username,
            password,
            first_name,
            last_name,
            phone_number,
            role,
            must_change_password,
        )
    except UserAlreadyExistsException:
        return None


def update_user(db, username: str, user):
    """Apply the editable profile fields of `user` to the stored account.

    The fields are named here rather than discovered from the incoming
    object. `vars(user)` wrote every attribute the request model happened to
    carry onto the columns that shared their names, so adding a field to any
    schema that reaches this helper made that column writable by whoever can
    call the route -- role and password included, without either appearing in
    a diff of this function.
    """
    db_user = get_user_by_username(db, username)
    # Returned rather than assumed present: setattr on None raises
    # AttributeError, which the caller sees as a 500 instead of a 404.
    if db_user is None:
        return None

    for field in UPDATABLE_PROFILE_FIELDS:
        value = getattr(user, field, None)
        if value:
            setattr(db_user, field, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    # Issuance and verification share one module so the algorithm used to
    # sign cannot drift from the algorithm accepted on the way back in.
    return encode_token(data, expires_delta)


def send_code_to_phone_number(phone_number: str, code: str):
    # normally this would send a code to the phone number using
    # a third party service
    print(f"Sending code {code} to phone number {phone_number}")
    return True
