def test_healthcheck_response_headers(anon_client):
    """
    Checks the response headers returned by the "/healthcheck" endpoint.

    Confirms that the endpoint responds with HTTP 200 and includes the
    "X-Powered-By" header in the response.
    """

    response = anon_client.get("/healthcheck")
    assert response.status_code == 200
    assert response.headers.get("X-Powered-By") is not None
