import logging
import subprocess

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

DF_TIMEOUT_SECONDS = 5

# The only directories the child is allowed to resolve a binary from.
SAFE_PATH = "/usr/bin:/bin"


def get_disk_usage(mount_point: str) -> str:
    """Report disk usage for a mount point.

    The command is built as an argument list with no shell, so the mount
    point is passed as a single argv entry and shell metacharacters in it
    carry no meaning.
    """
    try:
        result = subprocess.run(
            ["df", "-h", mount_point],
            capture_output=True,
            check=True,
            timeout=DF_TIMEOUT_SECONDS,
            # The child does not inherit this process's environment. Without
            # this it receives every variable the application was given,
            # including the signing key and the database password, and a
            # child that logs or echoes its environment leaks them. PATH is
            # fixed so the binary resolved is not decided by an inherited
            # value, and LC_ALL=C keeps the output shape stable rather than
            # dependent on the host's locale.
            env={"PATH": SAFE_PATH, "LC_ALL": "C"},
            # Started from a directory the application does not write to, so
            # a relative path in the child cannot reach anything it uploaded.
            cwd="/",
            # Nothing is written to the child, and leaving stdin attached
            # means a command that decides to prompt blocks until the
            # timeout instead of failing.
            stdin=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        # The detail goes to the log; the client gets a generic message with
        # no command string, path or traceback.
        logger.exception("df failed for mount_point=%s", mount_point)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read disk statistics",
        )

    return result.stdout.decode().strip()
