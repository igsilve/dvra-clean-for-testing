import os
import secrets
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
from enum import Enum


class ENV(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


ENVIRONMENT = ENV(os.getenv("ENV", ENV.PRODUCTION.value))


def generate_random_secret():
    return secrets.token_hex(32)


class Settings:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", generate_random_secret())
    CHEF_USERNAME = os.getenv("CHEF_USERNAME", "chef")

    JWT_VERIFY_SIGNATURE = os.getenv("JWT_VERIFY_SIGNATURE")

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", 5432)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "restaurant")

    TITLE: str = "RESTaurant API"
    DESCRIPTION: str = (
        "RESTaurant API - a restaurant ordering and menu management service."
    )
    VERSION: str = "1.0.0"

    # Allow switching between Postgres (default) and in-memory SQLite.
    # This keeps Postgres as the default behavior while enabling
    # self-contained in-memory runs when DB_BACKEND=memory is set.
    DB_BACKEND: str = os.getenv("DB_BACKEND", "postgres")

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        if not self.POSTGRES_PASSWORD:
            raise RuntimeError("POSTGRES_PASSWORD environment variable is required but not set")
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        server = quote_plus(self.POSTGRES_SERVER)
        db = quote_plus(self.POSTGRES_DB)
        return f"postgresql://{user}:{password}@{server}:{self.POSTGRES_PORT}/{db}"

    @property
    def SERVER_URL(self) -> str:
        return "https://localhost:8091/"

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
