"""The single place authorization is decided.

Routes declare the *permission* they need, not the roles that happen to have
it today. The difference matters when the role set changes: with roles named
at each call site, adding a "Manager" who can edit the menu means finding
every menu route and hoping none was missed. Here it is one line in
ROLE_PERMISSIONS.

Ownership lives here too. Role checks answer "may this kind of user do this
kind of thing"; they say nothing about whether *this* order belongs to
*this* customer. Keeping both in one module is what stops the second
question from being answered ad hoc in each handler, or forgotten.
"""

import enum
from dataclasses import dataclass
from typing import Optional, Set

from apis.auth.utils.jwt_auth import get_current_user
from audit_log import audit
from db.models import User, UserRole
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Query


class Permission(str, enum.Enum):
    READ_DISK_STATS = "read:disk_stats"
    READ_DEBUG_INFO = "read:debug_info"
    RESET_CHEF_PASSWORD = "manage:chef_password"
    MANAGE_MENU = "manage:menu"
    MANAGE_ROLES = "manage:roles"
    READ_DELIVERY_FEED = "read:delivery_feed"
    PLACE_ORDER = "order:create"
    READ_OWN_ORDERS = "order:read_own"


# The whole authorization model, in one table. A permission absent from a
# role's set is denied; there is no inheritance and no wildcard, so reading
# a row tells you exactly what that role can do.
ROLE_PERMISSIONS = {
    UserRole.CHEF: {
        Permission.READ_DISK_STATS,
        Permission.READ_DEBUG_INFO,
        Permission.RESET_CHEF_PASSWORD,
        Permission.MANAGE_MENU,
        Permission.MANAGE_ROLES,
        Permission.READ_DELIVERY_FEED,
    },
    UserRole.EMPLOYEE: {
        Permission.MANAGE_MENU,
        Permission.READ_DELIVERY_FEED,
    },
    UserRole.CUSTOMER: {
        Permission.PLACE_ORDER,
        Permission.READ_OWN_ORDERS,
    },
}


def permissions_for(role) -> Set[Permission]:
    """Permissions granted to a role, empty for anything unrecognised.

    Unknown roles get nothing rather than everything, so a role added to the
    enum without a row here fails closed.
    """
    if isinstance(role, str):
        try:
            role = UserRole(role)
        except ValueError:
            return set()
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(user: User, permission: Permission) -> bool:
    """Deny by default, including when there is nothing to decide about.

    A missing user or a user with no role used to raise AttributeError,
    which surfaces as a 500. That is not a refusal: it is an unhandled
    error that happens to stop the request, and the next caller who
    reaches this with a partially built context may not be so lucky.
    """
    if user is None:
        return False

    return permission in permissions_for(getattr(user, "role", None))


class Requires:
    """Route dependency declaring the permission the endpoint needs."""

    def __init__(self, permission: Permission):
        self.permission = permission

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if not has_permission(user, self.permission):
            # The caller is told nothing, and the log is told everything:
            # which identity, which role, which permission. The opaque
            # response and the detailed record are not in tension.
            audit(
                "authorization",
                outcome="denied",
                actor=user.username,
                actor_role=user.role,
                action=self.permission.value,
                reason="missing_permission",
            )
            # Deliberately the same opaque message for every denial: a
            # detailed one tells the caller which permission to go after.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized"
            )
        return user


@dataclass(frozen=True)
class AuthzContext:
    """Everything an authorization decision needs, in one immutable object.

    Service functions used to take a bare `item_id` and trust that whoever
    called them had already checked something. That makes the decision
    invisible at the point where the data is actually changed, and it means
    a second caller — a background job, a management command, a new route —
    inherits no protection at all.

    `actor` is always the server-derived user from the token, never a role
    or id supplied by the client. `resource` is the target loaded from the
    database, not attributes the caller asserted about it.
    """

    actor: User
    resource: object = None

    def require(self, permission: Permission) -> "AuthzContext":
        if not has_permission(self.actor, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized"
            )
        return self

    def require_ownership(self) -> "AuthzContext":
        """Authorize against the trusted resource, not a client-supplied id."""
        if self.resource is None:
            # No resource loaded means the decision cannot be made, so it
            # is refused rather than assumed.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized"
            )

        if has_permission(self.actor, Permission.READ_DELIVERY_FEED):
            return self

        if getattr(self.resource, "user_id", None) != self.actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized"
            )

        return self


def system_authz() -> AuthzContext:
    """Context for work the application does on its own behalf.

    Seeding runs before any user exists, so it cannot present one. Rather
    than making `authz` optional on the service functions — which would put
    the hole straight back, since an omitted argument is the easiest
    mistake to make — the bootstrap asks for this explicitly. The name is
    deliberately conspicuous: a call site holding a system context is one a
    reviewer should stop at.

    Never construct this from anything a request can influence.
    """
    return AuthzContext(actor=User(id=None, username="system", role=UserRole.CHEF))


def owned_by(query: Query, model, user: User) -> Query:
    """Narrow a query to rows the user owns.

    Expressed as a filter rather than a check after loading, so there is no
    moment where the object exists in memory without the ownership question
    having been asked. A handler that forgets the check cannot accidentally
    serialize someone else's row, because it never had it.

    Staff with the delivery-feed permission are exempt: their job requires
    reading orders they did not place.
    """
    if has_permission(user, Permission.READ_DELIVERY_FEED):
        return query
    return query.filter(model.user_id == user.id)


def may_use_self_service_password_reset(user: Optional[User]) -> bool:
    """Whether an account may reset its password via the phone-code flow.

    A rule about the subject of the operation rather than the caller, but it
    is still a role decision, so it lives here rather than inline in the
    handler where the next person would not know to look for it.
    """
    if user is None:
        return False
    role = user.role
    if isinstance(role, str):
        try:
            role = UserRole(role)
        except ValueError:
            return False
    return role is UserRole.CUSTOMER
