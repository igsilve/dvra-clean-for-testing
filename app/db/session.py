from typing import Generator
import logging
import time

from config import settings
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


logger = logging.getLogger("app.db.audit")


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
        db_url = URL.create(
            drivername="postgresql",
            username=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_SERVER,
            port=int(settings.POSTGRES_PORT),
            database=settings.POSTGRES_DB,
            query={"sslmode": settings.POSTGRES_SSL_MODE},
        )
        engine = create_engine(db_url)

    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, session_local


engine, SessionLocal = _create_engine_and_session()


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start_times = conn.info.get("query_start_time", [])
    if not start_times:
        return

    duration_ms = (time.perf_counter() - start_times.pop()) * 1000
    statement_type = statement.strip().split(" ", 1)[0].upper() if statement else "UNKNOWN"
    logger.info(
        "db_query_executed type=%s rowcount=%s duration_ms=%.2f",
        statement_type,
        cursor.rowcount,
        duration_ms,
    )


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
