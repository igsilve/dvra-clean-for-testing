def test_reset_chef_password_anonymous_returns_401(test_db, anon_client):
    response = anon_client.post("/admin/reset-chef-password")
    assert response.status_code == 401


def test_reset_chef_password_non_chef_returns_403(
    test_db, employee_client, customer_client
):
    for client in (employee_client, customer_client):
        response = client.post("/admin/reset-chef-password")
        assert response.status_code == 403


def test_reset_chef_password_source_address_grants_nothing(
    test_db, anon_client, mocker
):
    # The removed control trusted request.client.host, which a proxy hop can set.
    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = "127.0.0.1"

    response = anon_client.post("/admin/reset-chef-password")
    assert response.status_code == 401


def test_reset_chef_password_as_chef_returns_200(test_db, chef_client):
    # Rotating the privileged account's password now requires proving
    # possession of the current one, so a replayed token alone is not
    # enough to take the account over.
    response = chef_client.post(
        "/admin/reset-chef-password", json={"current_password": "password"}
    )
    assert response.status_code == 200
    assert response.json().get("password") is not None


def test_reset_chef_password_rejects_a_wrong_current_password(test_db, chef_client):
    response = chef_client.post(
        "/admin/reset-chef-password", json={"current_password": "not-the-password"}
    )
    assert response.status_code == 401

    # The refusal does not say whether the password or the authorization
    # was the problem.
    assert response.json().get("detail") == "Unauthorized"


def test_reset_chef_password_requires_the_step_up_field(test_db, chef_client):
    """A token alone, with no proof of the current password, is refused."""
    response = chef_client.post("/admin/reset-chef-password")
    assert response.status_code == 422


def test_stats_disk_returns_output_with_200(test_db, chef_client):
    response = chef_client.get(f"/admin/stats/disk")
    assert response.status_code == 200
    assert response.json().get("output") is not None


def test_stats_disk_unauthorised_returns_403(
    test_db, anon_client, employee_client, customer_client
):
    # Authorization is enforced by the shared RolesBasedAuthChecker rather
    # than an inline role comparison, so the refusal is a generic
    # "Unauthorized" that does not disclose which role is required.
    #
    # Note: this test requests anon_client alongside employee_client and
    # customer_client, which share one app instance, so the last fixture's
    # get_current_user override applies to all three clients. This first
    # request is therefore authenticated as a non-Chef user, not anonymous.
    # Anonymous access is covered separately in tests/security/test_controls.py.
    response = anon_client.get(f"/admin/stats/disk")
    assert response.status_code == 403
    assert response.json().get("detail") == "Unauthorized"

    response = employee_client.get(f"/admin/stats/disk")
    assert response.status_code == 403
    assert response.json().get("detail") == "Unauthorized"

    response = customer_client.get(f"/admin/stats/disk")
    assert response.status_code == 403
    assert response.json().get("detail") == "Unauthorized"
