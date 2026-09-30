from db.models import User, UserRole


def _a_customer(test_db):
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
    return user


def test_user_role_update_is_refused_for_customers(test_db, customer_client):
    """
    Exercises the PUT "/users/update_role" endpoint as a customer.

    This test previously asserted the opposite: that any authenticated
    customer could promote an account to Employee and receive HTTP 200. The
    endpoint accepts a username, so this was not even limited to the
    caller's own account.
    """
    user = _a_customer(test_db)

    response = customer_client.put(
        "/users/update_role",
        json={"username": "regular_customer", "role": "Employee"},
    )

    assert response.status_code == 403

    test_db.refresh(user)
    assert user.role == UserRole.CUSTOMER


def test_user_role_update_is_allowed_for_the_chef(test_db, chef_client):
    user = _a_customer(test_db)

    response = chef_client.put(
        "/users/update_role",
        json={"username": "regular_customer", "role": "Employee"},
    )

    assert response.status_code == 200
    # The response describes the account that changed, not the caller.
    assert response.json() == {
        "username": "regular_customer",
        "role": "Employee",
    }

    test_db.refresh(user)
    assert user.role == UserRole.EMPLOYEE


def test_an_unknown_role_is_rejected(test_db, chef_client):
    user = _a_customer(test_db)

    response = chef_client.put(
        "/users/update_role",
        json={"username": "regular_customer", "role": "Overlord"},
    )

    assert response.status_code == 422

    test_db.refresh(user)
    assert user.role == UserRole.CUSTOMER
