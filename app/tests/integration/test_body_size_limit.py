from config import settings

OVER_LIMIT = settings.MAX_BODY_BYTES + 1024


def test_oversized_declared_body_is_rejected(test_db, chef_client):
    payload = {"name": "x", "description": "A" * OVER_LIMIT, "price": 1.0}

    response = chef_client.put("/menu", json=payload)

    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"


def test_oversized_chunked_body_is_rejected(test_db, chef_client):
    def chunks():
        sent = 0
        while sent <= OVER_LIMIT:
            block = b"A" * 64 * 1024
            sent += len(block)
            yield block

    # No Content-Length, so the ceiling has to be enforced while streaming.
    response = chef_client.put(
        "/menu",
        content=chunks(),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413


def test_malformed_content_length_is_rejected(test_db, chef_client):
    response = chef_client.put(
        "/menu",
        content=b"{}",
        headers={"Content-Length": "not-a-number", "Content-Type": "application/json"},
    )

    assert response.status_code == 400


def test_body_within_the_ceiling_is_accepted(test_db, chef_client):
    payload = {
        "name": "Soup",
        "description": "B" * 1024,
        "price": 4.5,
        "category": "starter",
    }

    response = chef_client.put("/menu", json=payload)

    # Anything other than a size rejection: the ceiling must not affect
    # normally sized requests.
    assert response.status_code not in (400, 413)
