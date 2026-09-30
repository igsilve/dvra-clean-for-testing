from db.models import User, UserRole


def test_profile_update_cannot_target_another_account(test_db, customer_client):
    """
    Exercises the PUT "/profile" endpoint against someone else's account.

    This test previously created a second user, updated that user's profile
    from a different caller's session, and asserted the change succeeded with
    an HTTP 200. That is the bug, not the behaviour: the endpoint chose which
    account to edit from the username in the request body, so any
    authenticated caller could rewrite anyone's name and phone number by
    naming them. The account being edited now comes from the token.
    """

    user = User(
        username="someuser",
        password="password",
        first_name="someuser",
        last_name="",
        phone_number="1234567890",
        role=UserRole.CUSTOMER,
    )
    test_db.add(user)
    test_db.commit()

    user_update_data = {
        "username": "someuser",
        "first_name": "smile",
        "last_name": "chef",
        "phone_number": "123",
    }

    response = customer_client.put("/profile", json=user_update_data)

    assert response.status_code == 403
    test_db.refresh(user)
    assert user.first_name == "someuser"
    assert user.last_name == ""
    assert user.phone_number == "1234567890"


def test_profile_update_applies_to_the_callers_own_account(test_db, customer_client):
    """The allow path: editing your own profile still works."""

    user_update_data = {
        "username": "customer",
        "first_name": "smile",
        "last_name": "chef",
        "phone_number": "123",
    }

    response = customer_client.put("/profile", json=user_update_data)

    assert response.status_code == 200

    caller = test_db.query(User).filter(User.username == "customer").one()
    assert caller.first_name == "smile"
    assert caller.last_name == "chef"
    assert caller.phone_number == "123"


def test_profile_update_cannot_rename_the_account(test_db, customer_client):
    """username identifies the subject; it is not an editable field."""

    response = customer_client.put(
        "/profile",
        json={"username": "customer", "first_name": "renamed"},
    )

    assert response.status_code == 200
    assert test_db.query(User).filter(User.username == "customer").count() == 1
