"""Router mounting, with the authenticated and anonymous surfaces separated.

Every router below is in exactly one group, and the grouping is the point.
Previously they were mounted in a single undifferentiated list, so a router
was public or protected depending on what its individual routes happened to
declare — which is how `/debug` and `/delivery/orders` ended up reachable by
anyone. Nobody decided that; it was the default.

Adding a router now means choosing a group. The default choice is
AUTHENTICATED: putting a router in PUBLIC or MIXED is a visible decision in
review, and `tests/security/test_router_grouping.py` fails the build for a
router that is mounted without appearing in one of these lists.
"""

from apis.admin.service import router as admin_router
from apis.auth.service import router as auth_router
from apis.auth.utils import get_current_user
from apis.healthcheck.service import router as healthcheck_router
from apis.menu.service import router as menu_router
from apis.orders.service import router as orders_router
from apis.referrals.service import router as referrals_router
from apis.users.service import router as users_router
from fastapi import APIRouter, Depends

api_router = APIRouter()

# Authentication is required for the whole router, in addition to whatever
# each route requires for itself. A route added here without its own
# dependency is still refused to anonymous callers.
REQUIRES_AUTHENTICATION = [Depends(get_current_user)]

# Group 1 — anonymous by design.
PUBLIC_ROUTERS = {"healthcheck": healthcheck_router}

# Group 2 — every route requires an authenticated caller.
AUTHENTICATED_ROUTERS = {
    "orders": orders_router,
    "admin": admin_router,
    "users": users_router,
    "referrals": referrals_router,
}

# Group 3 — genuinely both, and each public route is justified in the
# PUBLIC_ROUTES allow-list that the route-table guard test checks against.
# `auth` issues credentials and so cannot require one to do it; `menu`
# serves the public menu for reading while every mutation is staff-only.
# These cannot take a router-level dependency, which is exactly why they
# are called out rather than quietly left out.
MIXED_ROUTERS = {"auth": auth_router, "menu": menu_router}

for router in PUBLIC_ROUTERS.values():
    api_router.include_router(router, prefix="")

api_router.include_router(
    orders_router, prefix="", tags=["orders"], dependencies=REQUIRES_AUTHENTICATION
)
api_router.include_router(
    admin_router, prefix="", tags=["admin"], dependencies=REQUIRES_AUTHENTICATION
)
api_router.include_router(
    users_router, prefix="", tags=["users"], dependencies=REQUIRES_AUTHENTICATION
)
api_router.include_router(
    referrals_router,
    prefix="",
    tags=["referrals"],
    dependencies=REQUIRES_AUTHENTICATION,
)

api_router.include_router(menu_router, prefix="", tags=["menu"])
api_router.include_router(auth_router, prefix="", tags=["auth"])
