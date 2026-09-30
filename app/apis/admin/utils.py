import logging
import subprocess

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

DF_TIMEOUT_SECONDS = 5


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
