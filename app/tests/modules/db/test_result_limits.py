import pytest
from db.models import MenuItem
from db.result_limits import MAX_ROWS, fetch_bounded
from fastapi import HTTPException


def _add_items(test_db, count):
    for i in range(count):
        test_db.add(
            MenuItem(
                name=f"Item {i}",
                description="",
                price=1.0,
                category="Main",
                image_base64="",
            )
        )
    test_db.commit()


def test_returns_rows_when_under_the_ceiling(test_db):
    _add_items(test_db, 3)

    rows = fetch_bounded(test_db.query(MenuItem), max_rows=5)

    assert len(rows) == 3


def test_returns_rows_when_exactly_at_the_ceiling(test_db):
    _add_items(test_db, 5)

    rows = fetch_bounded(test_db.query(MenuItem), max_rows=5)

    assert len(rows) == 5


def test_raises_413_when_over_the_ceiling(test_db):
    _add_items(test_db, 6)

    with pytest.raises(HTTPException) as excinfo:
        fetch_bounded(test_db.query(MenuItem), max_rows=5)

    assert excinfo.value.status_code == 413
    # Generic: the message must not disclose how many rows exist.
    assert "6" not in excinfo.value.detail


def test_default_ceiling_is_server_controlled():
    # The ceiling is a module constant, never read from request input.
    assert isinstance(MAX_ROWS, int)
    assert MAX_ROWS > 0
