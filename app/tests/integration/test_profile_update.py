import json

from db.models import User, UserRole


def test_profile_update_by_username(test_db, customer_client):
    """
    Exercises the PUT "/profile" endpoint.

    Creates a user, submits a profile update that targets that user by
    username, and confirms the update is applied (first name, last name and
    phone number are changed) with an HTTP 200 response.
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

    response = customer_client.put(f"/profile", content=json.dumps(user_update_data))
    assert response.status_code == 200
    assert user.first_name == "smile"
    assert user.last_name == "chef"
    assert user.phone_number == "123"
