"""Authorization is enforced where the data changes, not only at the route.

A route guard protects one caller. The service function underneath it is
reachable from anywhere in the process — a background task, a management
command, a future endpoint someone adds without remembering the guard. These
tests pin the second check so removing it fails here rather than silently in
whatever calls it next.
"""

import inspect

import pytest
from apis.auth.utils.authz import AuthzContext, Permission, system_authz
from apis.menu import utils as menu_utils
from apis.menu.schemas import MenuItemCreate
from db.models import User, UserRole
from fastapi import HTTPException

MUTATING_MENU_SERVICES = [
    menu_utils.create_menu_item,
    menu_utils.update_menu_item,
    menu_utils.delete_menu_item,
]


def _user(role: UserRole) -> User:
    return User(id=1, username="someone", role=role)


@pytest.mark.parametrize(
    "service", MUTATING_MENU_SERVICES, ids=lambda f: f.__name__
)
def test_mutating_service_requires_an_authorization_context(service):
    """The context is a required argument, so it cannot be forgotten.

    If it had a default, omitting it would be the easy mistake and the
    check would quietly not happen.
    """
    parameter = inspect.signature(service).parameters["authz"]

    assert parameter.default is inspect.Parameter.empty, (
        f"{service.__name__} gives 'authz' a default, so a caller that "
        "omits it skips the authorization check entirely"
    )


@pytest.mark.parametrize(
    "service", MUTATING_MENU_SERVICES, ids=lambda f: f.__name__
)
def test_mutating_service_refuses_a_caller_without_the_permission(
    service, test_db
):
    """A customer holding a context is still refused by the service."""
    context = AuthzContext(actor=_user(UserRole.CUSTOMER))

    with pytest.raises(HTTPException) as refusal:
        if service is menu_utils.create_menu_item:
            service(test_db, MenuItemCreate(name="x", price=1.0, category="c"), context)
        elif service is menu_utils.update_menu_item:
            service(
                test_db,
                1,
                MenuItemCreate(name="x", price=1.0, category="c"),
                context,
            )
        else:
            service(test_db, 1, context)

    assert refusal.value.status_code == 403


def test_refusal_happens_before_the_database_is_touched(test_db, monkeypatch):
    """The check is at the top, not after the row has been read or written."""

    def fail(*args, **kwargs):
        raise AssertionError(
            "the service queried the database before deciding the caller "
            "was allowed to be there"
        )

    monkeypatch.setattr(test_db, "query", fail)
    monkeypatch.setattr(test_db, "add", fail)

    with pytest.raises(HTTPException):
        menu_utils.delete_menu_item(
            test_db, 1, AuthzContext(actor=_user(UserRole.CUSTOMER))
        )


def test_context_carries_the_server_derived_user_not_a_claimed_role():
    """The decision reads the actor object, never a role the caller sent."""
    customer = _user(UserRole.CUSTOMER)
    context = AuthzContext(actor=customer)

    # Mimic a client asserting a role alongside its request.
    with pytest.raises(HTTPException):
        context.require(Permission.MANAGE_MENU)

    # And the context itself cannot be edited into a different answer.
    with pytest.raises(Exception):
        context.actor = _user(UserRole.CHEF)


def test_ownership_is_refused_when_no_resource_was_loaded():
    """An undecidable check denies rather than falls through to allow."""
    context = AuthzContext(actor=_user(UserRole.CUSTOMER), resource=None)

    with pytest.raises(HTTPException) as refusal:
        context.require_ownership()

    assert refusal.value.status_code == 403


def test_ownership_compares_against_the_loaded_resource():
    owner = User(id=7, username="owner", role=UserRole.CUSTOMER)
    someone_else = User(id=8, username="other", role=UserRole.CUSTOMER)

    class Resource:
        user_id = 7

    AuthzContext(actor=owner, resource=Resource()).require_ownership()

    with pytest.raises(HTTPException):
        AuthzContext(actor=someone_else, resource=Resource()).require_ownership()


def test_system_context_is_not_reachable_from_request_data():
    """Seeding needs a privileged context; requests must not be able to mint one."""
    context = system_authz()

    assert context.actor.id is None, (
        "the system context resolves to a real account id, so it could be "
        "confused with a user and its actions attributed to them"
    )
    assert inspect.signature(system_authz).parameters == {}, (
        "system_authz takes an argument, which means something could be "
        "passed in from a request to influence what it returns"
    )
