from apis.auth.schemas import TokenData
from apis.auth.utils.utils import get_user_by_username
from config import settings
from db.session import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing_extensions import Annotated

SECRET_KEY = settings.JWT_SECRET_KEY
# A literal, single-entry list. Deriving this from configuration or echoing
# the token's own header would let a caller choose "none" and authenticate
# with an unsigned token.
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Declared `def` so FastAPI runs it in the threadpool: the user lookup is a
# synchronous SQLAlchemy query, and this dependency runs on every authenticated
# request. On the event loop it would stall every other request in the process.
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            # Verification is unconditional: there is no flag that can turn
            # it off. python-jose spells the presence checks as require_*
            # booleans and ignores unrecognised option keys, so a PyJWT-style
            # {"require": [...]} here would be silently dropped and a token
            # carrying no exp at all would be accepted as non-expiring.
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require_exp": True,
                "require_sub": True,
            },
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
