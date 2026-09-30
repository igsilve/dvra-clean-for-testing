from db.models import MenuItem


def _a_menu_item(test_db):
    menu_item = MenuItem(
        name="Chicken Burrito",
        price=10.99,
        category="",
        description="",
        image_base64="",
    )
    test_db.add(menu_item)
    test_db.commit()
    return menu_item


def test_menu_item_deletion_is_refused_for_customers(test_db, customer_client):
    """
    Exercises the DELETE "/menu/{id}" endpoint as a customer.

    This test previously asserted the opposite: that a customer could delete
    any menu item and receive HTTP 204. Deleting from the menu is a staff
    action, and create and update already required the role; delete was the
    one that did not.
    """
    menu_item = _a_menu_item(test_db)

    response = customer_client.delete(f"/menu/{menu_item.id}")

    assert response.status_code == 403
    assert test_db.query(MenuItem).filter(MenuItem.id == menu_item.id).first()


def test_menu_item_deletion_is_allowed_for_employees(test_db, employee_client):
    """The allow path, so the control is not simply blocking everyone."""
    menu_item = _a_menu_item(test_db)

    response = employee_client.delete(f"/menu/{menu_item.id}")

    assert response.status_code == 204
    assert (
        test_db.query(MenuItem).filter(MenuItem.id == menu_item.id).first() is None
    )
