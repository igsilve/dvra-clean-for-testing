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
    response = chef_client.post("/admin/reset-chef-password")
    assert response.status_code == 200
    assert response.json().get("password") is not None


def test_stats_disk_returns_output_with_200(test_db, chef_client):
    response = chef_client.get(f"/admin/stats/disk")
    assert response.status_code == 200
    assert response.json().get("output") is not None


def test_stats_disk_unauthorised_returns_403(
    test_db, anon_client, employee_client, customer_client
):
    response = anon_client.get(f"/admin/stats/disk")
    assert response.status_code == 403
    assert (
        response.json().get("detail")
        == "Only Chef is authorized to get current disk stats!"
    )

    response = employee_client.get(f"/admin/stats/disk")
    assert response.status_code == 403
    assert (
        response.json().get("detail")
        == "Only Chef is authorized to get current disk stats!"
    )

    response = customer_client.get(f"/admin/stats/disk")
    assert response.status_code == 403
    assert (
        response.json().get("detail")
        == "Only Chef is authorized to get current disk stats!"
    )
