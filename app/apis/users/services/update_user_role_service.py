from apis.auth.utils import Permission, Requires, get_current_user, update_user
from apis.users.schemas import UserRoleUpdate
from audit_log import audit
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
    # Granting privilege is itself the highest privilege in this system.
    # Previously any authenticated account could call this with any
    # username, so a customer could promote themselves to Employee — the
    # only thing refused was the word "Chef", which is not a control, just
    # a smaller escalation.
    auth=Depends(Requires(Permission.MANAGE_ROLES)),
):
    # The role arrives as a free-form string, so it is matched against the
    # enum rather than written through to the column as given.
    try:
        new_role = models.UserRole(user.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unknown role",
        )

    db_user = update_user(db, user.username, user)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    previous_role = db_user.role.value if db_user.role else None
    db_user.role = new_role
    # A privilege change must not leave tokens minted under the old role
    # usable, so outstanding tokens for the affected account are revoked.
    invalidate_issued_tokens(db_user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Recorded after the commit, so the trail says what happened rather
    # than what was attempted; the refusals above are recorded by the
    # access-audit middleware as denials on this path.
    audit(
        "privilege_change",
        actor=current_user.username,
        actor_role=current_user.role,
        subject=db_user.username,
        subject_role=previous_role,
        action=f"role_set_to_{new_role.value}",
    )

    # The affected user, not the caller. Returning the caller reported the
    # chef's own unchanged role as though it were the result.
    return UserRoleUpdate(username=db_user.username, role=db_user.role.value)
