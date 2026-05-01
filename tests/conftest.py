"""Pytest fixtures.

Uses a Postgres testcontainer when Docker is available; otherwise the test
session is skipped (we will not silently fall back to SQLite — Postgres parity is
non-negotiable for the suite).
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


def _start_postgres() -> str | None:
    """Try to start a Postgres testcontainer. Return DSN or None on failure."""
    try:
        from testcontainers.postgres import PostgresContainer
    except Exception:  # noqa: BLE001
        return None
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except Exception as exc:  # noqa: BLE001
        print(f"[conftest] testcontainers unavailable: {exc}")
        return None
    pytest._pg_container = container  # type: ignore[attr-defined]
    raw = container.get_connection_url()  # postgresql+psycopg2://...
    return raw.replace("+psycopg2", "+psycopg")


@pytest.fixture(scope="session", autouse=True)
def _configure_env() -> Iterator[None]:
    dsn = os.environ.get("TEST_DATABASE_URL") or _start_postgres()
    if dsn is None:
        pytest.skip("Docker / testcontainers unavailable; skipping integration suite.")
    os.environ["DATABASE_URL"] = dsn
    os.environ["FLASK_ENV"] = "testing"
    os.environ["RATELIMIT_STORAGE_URI"] = "memory://"
    os.environ["LOG_JSON"] = "false"
    yield
    container = getattr(pytest, "_pg_container", None)
    if container is not None:
        container.stop()


@pytest.fixture()
def app():
    from sqlalchemy import text

    from app import create_app
    from app.extensions import db

    application = create_app("testing")
    with application.app_context():
        # Ensure required PG extensions exist before migrations run.
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        db.session.commit()

        # Run migrations to head.
        from flask_migrate import upgrade as _upgrade

        _upgrade()
        yield application
        # Clean up between tests by truncating user data.
        db.session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    from app.extensions import db

    return db.session
