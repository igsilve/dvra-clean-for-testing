from db.models import MenuItem


def test_menu_item_deletion(test_db, customer_client):
    """
    Exercises the DELETE "/menu/{id}" endpoint.

    Creates a menu item and confirms it can be deleted through the endpoint,
    returning HTTP 204.
    """

    menu_item = MenuItem(
        name="Chicken Burrito",
        price=10.99,
        category="",
        description="",
        image_base64="",
    )
    test_db.add(menu_item)
    test_db.commit()

    response = customer_client.delete(f"/menu/{menu_item.id}")
    assert response.status_code == 204
