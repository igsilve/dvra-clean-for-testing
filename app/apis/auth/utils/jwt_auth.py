from apis.auth.schemas import TokenData
from apis.auth.utils.utils import get_user_by_username
from db.session import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jwt_tokens import decode_token
from sqlalchemy.orm import Session
from typing_extensions import Annotated

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
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    # A token minted before the account's last credential or privilege change
    # must stop working. A token with no `ver` claim predates this check and
    # is refused rather than trusted, so the check fails closed.
    if payload.get("ver") != (user.token_version or 0):
        raise credentials_exception

    return user
