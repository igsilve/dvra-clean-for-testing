import os
from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv
from sqlalchemy.engine import URL

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
from enum import Enum


class ENV(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


def _required_environment() -> ENV:
    """Read the deployment environment or refuse to start.

    The previous default was PRODUCTION while every other default in this
    module was a development convenience, so an unset ENV produced a process
    that called itself production and was configured like a laptop. Defaulting
    the other way would be worse: a real deployment would silently enable
    debug behaviour. Neither default is safe, so there is none.
    """
    raw = os.getenv("ENV")

    if not raw:
        raise RuntimeError(
            "ENV must be set explicitly to one of: "
            + ", ".join(member.value for member in ENV)
        )

    try:
        return ENV(raw)
    except ValueError:
        # ENV() raises a bare "'x' is not a valid ENV", which does not say
        # what the valid values are.
        raise RuntimeError(
            f"ENV={raw!r} is not a recognised environment; expected one of: "
            + ", ".join(member.value for member in ENV)
        ) from None


ENVIRONMENT = _required_environment()


# 256 bits, the floor for an HMAC key that is the sole thing standing
# between a forged token and a trusted identity.
MIN_SECRET_LENGTH = 32


def _required_secret(name: str) -> str:
    """Read a secret from the environment or refuse to start.

    There is deliberately no default and nothing generated here. A
    fallback key means a misconfigured deployment still boots, signs
    tokens with something nobody chose, and looks healthy; the previous
    fallback was six decimal digits, which is a million guesses. Failing
    at import turns that silent weakness into an obvious outage.

    The value is never echoed in the error.
    """
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"{name} must be supplied by the environment or secret store; "
            "there is no default"
        )

    if len(value) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"{name} must be at least {MIN_SECRET_LENGTH} characters"
        )

    return value


def _required(name: str) -> str:
    """Read a non-secret setting that still must not have a default.

    Separate from `_required_secret` because these values have no length
    floor; the point is only that nothing is assumed. The previous defaults
    named the privileged account "chef" and the database password "password",
    which are the first two guesses anyone makes, and they applied silently
    whenever the environment was incomplete.
    """
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"{name} must be supplied by the environment; there is no default"
        )

    return value


# Read before the class body so the database settings below can be required
# conditionally; `Settings.DB_BACKEND` does not exist yet at that point.
_DB_BACKEND = os.getenv("DB_BACKEND", "postgres")


def _db_required(name: str) -> str:
    """Require a database setting, unless no database is in use.

    With DB_BACKEND=memory the process never opens a connection, so these
    values are not settings with a weak default; they are settings with no
    consumer. Requiring them anyway would force every test run to invent a
    password that nothing reads.
    """
    if _DB_BACKEND == "memory":
        return ""

    return _required(name)


class Settings:
    JWT_SECRET_KEY: str = _required_secret("JWT_SECRET_KEY")

    # Required rather than defaulted to "chef": a well-known account name is
    # half of a credential, and it is the half an attacker gets for free.
    CHEF_USERNAME: str = _required("CHEF_USERNAME")

    # There is deliberately no JWT_VERIFY_SIGNATURE setting. Signature
    # verification is not configurable, so no environment value can disable it.

    # Token issuer and audience. Not secrets, so a default is fine, but both
    # are validated on decode, so a token minted for another audience or by
    # another issuer is rejected rather than merely labelled.
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "restaurant-api")
    JWT_AUDIENCE: str = os.getenv("JWT_AUDIENCE", "restaurant-api-clients")

    # Key for deriving the stored form of one-time reset codes. Required
    # rather than generated: this deployment runs several workers, and a
    # per-process key would mean a code issued by one worker fails to
    # verify on another.
    OTP_HMAC_KEY: str = _required_secret("OTP_HMAC_KEY")

    # Credentials for the database, required whenever one is actually used.
    # The previous defaults were "admin" and "password", which meant an
    # incomplete environment produced a running service with the credentials
    # every scanner tries first. Under DB_BACKEND=memory there is no
    # connection and no credential, so these are unused rather than defaulted.
    POSTGRES_USER: str = _db_required("POSTGRES_USER")
    POSTGRES_PASSWORD: str = _db_required("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = _db_required("POSTGRES_SERVER")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = _db_required("POSTGRES_DB")

    # Host and origin allow-lists. Comma-separated in the environment; the
    # defaults cover local development only and are deliberately not wildcards.
    ALLOWED_HOSTS: list[str] = [
        h.strip()
        for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        if h.strip()
    ]
    # Credentialed CORS is enabled, so a wildcard origin would let any site
    # read authenticated responses. Drop "*" rather than trusting the operator
    # to never set it.
    ALLOWED_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:8091,http://127.0.0.1:8091"
        ).split(",")
        if o.strip() and o.strip() != "*"
    ]

    # Outbound integrations. Every remote component this service talks to is
    # named here explicitly: an empty allow-list means the feature is off,
    # never "anything goes". Tokens are the credential this service presents
    # so the remote side can authenticate it in turn.
    ALLOWED_IMAGE_HOSTS: list[str] = [
        h.strip()
        for h in os.getenv("ALLOWED_IMAGE_HOSTS", "").split(",")
        if h.strip() and h.strip() != "*"
    ]
    CDN_TOKEN: str = os.getenv("CDN_TOKEN", "")

    # PEM-encoded public key used to check the signature on remote content
    # before it is stored. It arrives through the environment, which is the
    # out-of-band channel: a key shipped alongside the content it verifies
    # proves nothing, because whoever can replace one can replace both.
    # Empty means no publisher has been configured, in which case content
    # is accepted on its digest alone.
    CONTENT_SIGNING_PUBLIC_KEY_PEM: str = os.getenv(
        "CONTENT_SIGNING_PUBLIC_KEY_PEM", ""
    )

    DELIVERY_API_BASE: str = os.getenv("DELIVERY_API_BASE", "")
    DELIVERY_API_TOKEN: str = os.getenv("DELIVERY_API_TOKEN", "")

    # (connect, read) seconds for every outbound call.
    OUTBOUND_TIMEOUT: tuple = (3, 5)

    # Request-size ceilings enforced by middleware.
    MAX_BODY_BYTES: int = int(os.getenv("MAX_BODY_BYTES", 1 * 1024 * 1024))
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", 5 * 1024 * 1024))

    ENVIRONMENT: ENV = ENVIRONMENT

    TITLE: str = "RESTaurant API"
    DESCRIPTION: str = (
        "RESTaurant API - a restaurant ordering and menu management service."
    )
    VERSION: str = "1.0.0"

    # Allow switching between Postgres (default) and in-memory SQLite.
    # This keeps Postgres as the default behavior while enabling
    # self-contained in-memory runs when DB_BACKEND=memory is set.
    DB_BACKEND: str = os.getenv("DB_BACKEND", "postgres")

    # How the connection to Postgres is protected. `require` is the weakest
    # value that actually encrypts; `prefer` and below fall back to
    # plaintext silently, which is the failure this setting exists to
    # avoid, so they are refused. Supplying a CA through
    # POSTGRES_SSLROOTCERT upgrades this to `verify-full`, which is the
    # only value that also authenticates the server rather than merely
    # encrypting to whoever answered.
    POSTGRES_SSLROOTCERT: str = os.getenv("POSTGRES_SSLROOTCERT", "")
    POSTGRES_SSLMODE: str = os.getenv("POSTGRES_SSLMODE", "require")

    @property
    def DATABASE_URL(self) -> Union[URL, str]:
        """Assemble the connection URL from components, never by interpolation.

        The previous form built the whole string with an f-string, which meant
        any delimiter inside a value was read as structure. A password
        containing `@` moved the host; one containing `?host=elsewhere`
        appended a connection parameter, and libpq's later occurrence wins, so
        the credential decided where the credential was sent. That is
        connection string parameter pollution, and no amount of care in
        choosing passwords prevents it, because the value often comes from a
        secret store rather than from a person.

        `URL.create` takes each component separately and escapes it for its
        own position, so a delimiter in a value stays inside that value. The
        object is passed to `create_engine` without being stringified, which
        also keeps the password out of anything that logs the URL.
        """
        if self.DB_BACKEND == "memory":
            return "sqlite://"

        if self.POSTGRES_SSLMODE not in ("require", "verify-ca", "verify-full"):
            raise RuntimeError(
                "POSTGRES_SSLMODE must be require, verify-ca or verify-full; "
                f"{self.POSTGRES_SSLMODE!r} permits an unencrypted connection"
            )

        parameters = {"sslmode": self.POSTGRES_SSLMODE}
        if self.POSTGRES_SSLROOTCERT:
            parameters["sslmode"] = "verify-full"
            parameters["sslrootcert"] = self.POSTGRES_SSLROOTCERT

        return URL.create(
            "postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=int(self.POSTGRES_PORT),
            database=self.POSTGRES_DB,
            query=parameters,
        )

    @property
    def SERVER_URL(self) -> str:
        return "http://localhost:8091/"

    @property
    def SERVERS(self) -> list[dict]:
        return [{"url": self.SERVER_URL, "description": self.SERVER_DESCRIPTION}]

    @property
    def ROOT_PATH(self) -> str:
        return ""

    @property
    def SERVER_DESCRIPTION(self) -> str:
        return "Local API server"


settings = Settings()
