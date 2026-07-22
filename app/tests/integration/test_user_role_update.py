import json

from db.models import User, UserRole


def test_user_role_update(test_db, customer_client):
    """
    Exercises the PUT "/users/update_role" endpoint.

    Creates a customer user, submits a role update to "Employee", and
    confirms the role is updated with an HTTP 200 response.
    """

    user = User(
        username="regular_customer",
        password="password",
        first_name="customer",
        last_name="",
        phone_number="1234567890",
        role=UserRole.CUSTOMER,
    )
    test_db.add(user)
    test_db.commit()

    user_update_data = {
        "username": "regular_customer",
        "role": "Employee",
    }

    response = customer_client.put(
        f"/users/update_role", content=json.dumps(user_update_data)
    )
    assert response.status_code == 200
    assert user.role == "Employee"
