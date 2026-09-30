import pytest
from db.models import User, UserRole


def test_menu_item_image_import_refuses_internal_targets(
    test_db, employee_client, requests_mock, mocker
):
    """
    Exercises the PUT "/menu" endpoint image import feature.

    The endpoint accepts an "image_url" and downloads the target. This test
    points it at a loopback address so that a successful fetch would mean the
    server can be used to reach its own internal endpoints, which is the
    server-side request forgery this must refuse.

    This test previously asserted the opposite: it pointed the importer at
    "/admin/reset-chef-password" and required the leaked credential to be
    stored base64 on the created menu item.

    It passes because the host allow-list added under T558 refuses any host
    the service was not configured to trust, loopback included. T7360/T1365
    still own the general egress question.
    """

    chef_user = User(
        username="chef",
        password="password",
        first_name="",
        last_name="",
        phone_number="",
        role=UserRole.CHEF,
    )
    test_db.add(chef_user)
    test_db.commit()

    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = "127.0.0.1"

    requests_mock.get(
        "http://localhost:8000/admin/reset-chef-password",
        json={"password": "should-never-be-fetched"},
    )

    menu_item = {
        "name": "Item",
        "price": 0.00,
        "category": "",
        "description": "",
        "image_url": "http://localhost:8000/admin/reset-chef-password",
    }

    response = employee_client.put("/menu", json=menu_item)

    assert response.status_code in (400, 422)
    assert "should-never-be-fetched" not in response.text
