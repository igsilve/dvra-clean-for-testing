def test_disk_stats_with_parameters(test_db, chef_client):
    """
    Verifies the "/admin/stats/disk" endpoint. The endpoint accepts a
    "parameters" query parameter that is forwarded to the "df" command
    used to report disk usage on the server.

    This test passes extra input through "parameters" and checks that the
    resulting command output is returned in the response body.
    """

    # request disk stats while passing extra input through "parameters"
    response = chef_client.get(
        f"/admin/stats/disk?parameters=%26%26echo%20dvra_probe_ok"
    )
    assert response.status_code == 200
    assert "dvra_probe_ok" in response.json().get("output")
