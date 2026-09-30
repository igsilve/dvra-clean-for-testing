def test_healthcheck_response_headers(anon_client):
    """
    Checks the response headers returned by the "/healthcheck" endpoint.

    Confirms that the endpoint responds with HTTP 200 and does not disclose the
    runtime stack through a "X-Powered-By" or "Server" banner.
    """

    response = anon_client.get("/healthcheck")
    assert response.status_code == 200
    assert response.headers.get("X-Powered-By") is None
    assert response.headers.get("Server") is None


def test_healthcheck_body_is_constrained(anon_client):
    """The response model exposes a liveness flag and nothing else."""

    response = anon_client.get("/healthcheck")
    assert response.json() == {"ok": True}
