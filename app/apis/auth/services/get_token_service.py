from datetime import timedelta

from apis.auth.schemas import Token
from apis.auth.utils import authenticate_user, create_access_token
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from rate_limiting import limiter
from sqlalchemy.orm import Session
from typing_extensions import Annotated

ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()


@router.post("/token")
@limiter.limit("10/minute")
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    client_ip = request.client.host if request.client else "unknown"
    user = authenticate_user(db, form_data.username, form_data.password, client_ip=client_ip)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
