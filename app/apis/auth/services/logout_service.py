from apis.auth.utils.jwt_auth import ALGORITHM, SECRET_KEY, oauth2_scheme
from apis.auth.utils.token_denylist import revoke_token
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from typing_extensions import Annotated

router = APIRouter()


@router.post("/logout", status_code=200)
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    """Revoke the current JWT so it cannot be reused after logout."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            revoke_token(jti, float(exp))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return {"detail": "Logged out successfully"}
