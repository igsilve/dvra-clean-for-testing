import logging
from typing import Generator

from config import settings
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_db_logger = logging.getLogger("audit.db")

_WRITE_KEYWORDS = {"INSERT", "UPDATE", "DELETE"}


def _create_engine_and_session():
    sqlalchemy_database_url = settings.DATABASE_URL

    # When using in-memory SQLite, we need StaticPool to share the same
    # in-memory database across all threads, and check_same_thread=False
    # to allow FastAPI's thread pool to access it.
    if sqlalchemy_database_url == "sqlite://":
        engine = create_engine(
            sqlalchemy_database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        ssl_args = {}
        import os as _os
        if _os.getenv("DB_SSL_CA"):
            ssl_args = {
                "sslmode": "verify-full",
                "sslrootcert": _os.getenv("DB_SSL_CA"),
            }
        engine = create_engine(sqlalchemy_database_url, connect_args=ssl_args)

    @event.listens_for(engine, "before_cursor_execute")
    def _log_db_writes(conn, cursor, statement, parameters, context, executemany):
        first_word = statement.strip().split(None, 1)[0].upper() if statement.strip() else ""
        if first_word in _WRITE_KEYWORDS:
            _db_logger.info("db_write op=%s stmt=%.200s", first_word, statement)

    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, session_local


engine, SessionLocal = _create_engine_and_session()


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
