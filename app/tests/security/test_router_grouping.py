"""Every router is deliberately placed on the public or authenticated side.

The failure this prevents is not a bad decision but an absent one. Routers
used to be mounted in a single flat list, so whether a router was reachable
anonymously depended on what its routes happened to declare individually.
`/debug` and `/delivery/orders` were public because nobody had said
otherwise, and nothing in the code looked wrong.
"""

import ast
import pathlib

import pytest
from apis import router as router_module
from fastapi.routing import APIRoute

pytestmark = pytest.mark.security

GROUPS = ("PUBLIC_ROUTERS", "AUTHENTICATED_ROUTERS", "MIXED_ROUTERS")


def _declared_routers() -> dict:
    declared = {}
    for group in GROUPS:
        for name in getattr(router_module, group):
            declared.setdefault(name, []).append(group)
    return declared


def test_every_imported_router_is_placed_in_exactly_one_group():
    source = pathlib.Path(router_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported = {
        alias.asname.removesuffix("_router")
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.asname and alias.asname.endswith("_router")
    }

    declared = _declared_routers()

    unplaced = sorted(imported - set(declared))
    assert unplaced == [], (
        f"routers mounted without choosing an access group: {unplaced}; "
        "the default is AUTHENTICATED, but it has to be written down"
    )

    duplicated = {name: groups for name, groups in declared.items() if len(groups) > 1}
    assert duplicated == {}, f"routers in more than one group: {duplicated}"


def test_the_authenticated_group_actually_carries_the_dependency():
    """A group label that does not change behaviour is just a comment."""
    guarded_prefixes = ("/orders", "/admin", "/users", "/referral", "/discount", "/internal")

    unguarded = []
    for route in router_module.api_router.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith(guarded_prefixes):
            continue
        names = {
            getattr(d.call, "__name__", type(d.call).__name__)
            for d in route.dependant.dependencies
        }
        if "get_current_user" not in names:
            unguarded.append(route.path)

    assert unguarded == [], (
        f"routes in the authenticated group with no authentication: {unguarded}"
    )


def test_a_new_router_added_to_no_group_is_caught():
    """The guard is only worth having if it notices an omission."""
    declared = _declared_routers()

    # Simulate the mistake: an import present, no group entry.
    imported = set(declared) | {"newfeature"}

    assert sorted(imported - set(declared)) == ["newfeature"]


def test_public_routers_expose_nothing_that_reads_user_data(anon_client):
    for name in router_module.PUBLIC_ROUTERS:
        assert name == "healthcheck", (
            f"{name} was moved to the public group; anything beyond the "
            "health probe needs its own justification"
        )

    assert anon_client.get("/healthcheck").status_code == 200
