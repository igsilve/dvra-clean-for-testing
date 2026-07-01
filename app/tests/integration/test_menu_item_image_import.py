import base64
import json

from db.models import User, UserRole


def test_menu_item_image_import_from_url(
    test_db, employee_client, anon_client, requests_mock, mocker
):
    """
    Exercises the PUT "/menu" endpoint image import feature.

    The endpoint accepts an "image_url", downloads the target, and stores the
    response as a base64 encoded value on the menu item. This test provides a
    URL pointing at the "/admin/reset-chef-password" endpoint and confirms the
    fetched content is stored on the created item.
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

    # mock the request client host and the outbound requests library response
    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = "127.0.0.1"

    def reset_callback(request, context):
        return anon_client.get("/admin/reset-chef-password").json()

    requests_mock.get(
        "http://localhost:8000/admin/reset-chef-password",
        json=reset_callback,
    )

    menu_item = {
        "name": "Item",
        "price": 0.00,
        "category": "",
        "description": "",
        "image_url": "http://localhost:8000/admin/reset-chef-password",
    }

    response = employee_client.put(f"/menu", content=json.dumps(menu_item))
    assert response.status_code == 201

    base64_reset_result = response.json().get("image_base64")
    reset_result = json.loads(base64.b64decode(base64_reset_result))

    assert reset_result.get("password") is not None
