def test_disk_stats_rejects_injected_shell_input(test_db, chef_client):
    """
    Verifies the "/admin/stats/disk" endpoint does not forward caller input
    to a shell.

    The endpoint used to accept a free-text "parameters" value that was
    concatenated into a "df -h ..." string and run with shell=True. It now
    accepts only a mount point from a fixed set, so an injected command is
    rejected before the handler runs and never executes.
    """

    response = chef_client.get(
        "/admin/stats/disk?mount_point=%26%26echo%20dvra_probe_ok"
    )

    assert response.status_code == 422
    assert "dvra_probe_ok" not in response.text


def test_disk_stats_returns_usage_for_an_allowed_mount_point(test_db, chef_client):
    response = chef_client.get("/admin/stats/disk", params={"mount_point": "/"})

    assert response.status_code == 200
    assert response.json().get("output")


def test_disk_stats_rejects_an_unlisted_mount_point(test_db, chef_client):
    response = chef_client.get("/admin/stats/disk", params={"mount_point": "/etc"})

    assert response.status_code == 422
