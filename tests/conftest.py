"""Pytest fixtures.

Tests require a local Postgres. Set TEST_DATABASE_URL to override the default
(`postgresql+psycopg://robot:robot@localhost:5432/robot_test`). The suite skips
itself when the database is unreachable.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DEFAULT_TEST_DSN = "sqlite:///./robotik_test.db"


@pytest.fixture(scope="session", autouse=True)
def _configure_env() -> Iterator[None]:
    dsn = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DSN)
    try:
        engine = create_engine(dsn)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
    except OperationalError as exc:
        pytest.skip(f"Postgres not reachable at {dsn}: {exc}")

    os.environ["DATABASE_URL"] = dsn
    os.environ["FLASK_ENV"] = "testing"
    os.environ["RATELIMIT_STORAGE_URI"] = "memory://"
    os.environ["LOG_JSON"] = "false"
    yield


@pytest.fixture()
def app():
    from app import create_app
    from app.extensions import db

    application = create_app("testing")
    with application.app_context():
        from flask_migrate import upgrade as _upgrade

        _upgrade()
        yield application
        db.session.execute(text("DELETE FROM users"))
        db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    from app.extensions import db

    return db.session
