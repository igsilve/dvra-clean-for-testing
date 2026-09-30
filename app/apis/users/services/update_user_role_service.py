from apis.auth.utils import get_current_user, update_user
from apis.users.schemas import UserRoleUpdate
from db import models
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from jwt_tokens import invalidate_issued_tokens
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.put("/users/update_role", response_model=UserRoleUpdate)
def update_user_role(
    user: UserRoleUpdate,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if user.role == models.UserRole.CHEF.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only Chef is authorized to add Chef role!",
        )

    db_user = update_user(db, user.username, user)
    # A privilege change must not leave tokens minted under the old role
    # usable, so outstanding tokens for the affected account are revoked.
    invalidate_issued_tokens(db_user)
    db.add(db_user)
    db.commit()

    return current_user
