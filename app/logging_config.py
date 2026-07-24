import logging
import os
import stat
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.getenv("LOG_DIR", "/var/log/app")
_LOG_FILE = os.path.join(_LOG_DIR, "audit.log")
_MAX_BYTES = 10_000_000
_BACKUP_COUNT = 5

_FMT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_audit_logging() -> None:
    """Set up rotating audit log. Falls back to stderr if log directory is unavailable."""
    handlers: list[logging.Handler] = []

    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT
        )
        # Restrict log file to owner read/write only (no group/other access)
        os.chmod(_LOG_FILE, stat.S_IRUSR | stat.S_IWUSR)
        handlers.append(file_handler)
    except OSError:
        pass  # container may not have /var/log/app — stderr fallback is fine

    handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format=_FMT,
        handlers=handlers,
    )


audit_logger = logging.getLogger("audit")


def log_registry_access(user_id: int, registry: str, action: str) -> None:
    """Log access to sensitive data registries (container, secret, image stores)."""
    audit_logger.info(
        "registry_access user_id=%s registry=%s action=%s",
        user_id,
        registry,
        action,
    )
