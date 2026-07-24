"""
Startup dependency version guards (T186).
Fails hard if any critical package is below its approved minimum version.
"""
from importlib.metadata import PackageNotFoundError, version

from packaging.version import Version

_MINIMUM_PATCHED_VERSIONS: dict[str, str] = {
    "fastapi": "0.100.0",
    "pydantic": "2.0.0",
    "sqlalchemy": "2.0.0",
    "python-jose": "3.3.0",
    "passlib": "1.7.4",
    "slowapi": "0.1.8",
    "cryptography": "41.0.0",
}


_OVER_PRIVILEGED_DB_USERS = {"root", "admin", "sa", "dbo", "postgres", "superuser"}


def assert_db_user_is_restricted() -> None:
    """Warn (not fail) if the configured DB user looks over-privileged."""
    import logging
    import os

    db_user = os.getenv("POSTGRES_USER", "").lower()
    if db_user in _OVER_PRIVILEGED_DB_USERS:
        logging.getLogger("audit").warning(
            "db_user_overprivileged user=%s — production deployments should use a "
            "restricted application account with SELECT/INSERT/UPDATE/DELETE only",
            db_user,
        )


def assert_patched_dependencies() -> None:
    """Raise RuntimeError if any critical package is absent or below minimum."""
    failures: list[str] = []
    for package, minimum in _MINIMUM_PATCHED_VERSIONS.items():
        try:
            installed = version(package)
        except PackageNotFoundError:
            failures.append(f"{package}: NOT INSTALLED (minimum {minimum})")
            continue
        if Version(installed) < Version(minimum):
            failures.append(f"{package}: {installed} < {minimum} (minimum)")
    if failures:
        raise RuntimeError(
            "Startup aborted — packages below approved minimum versions:\n"
            + "\n".join(failures)
        )
