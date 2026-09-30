from apis.auth.utils import get_current_user
from audit_log import audit
from db.models import User
from fastapi import Depends, HTTPException


class RolesBasedAuthChecker:
    def __init__(
        self,
        required_roles,
    ):
        self.required_roles = required_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.required_roles:
            # The refusal is recorded here rather than only as a 403 in the
            # access log, because the useful part is which identity asked
            # for what -- the status code alone does not say.
            audit(
                "authorization",
                outcome="denied",
                actor=user.username,
                actor_role=user.role,
                reason="insufficient_role",
            )
            raise HTTPException(status_code=403, detail="Unauthorized")

        return True
