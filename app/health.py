"""Liveness and readiness endpoints (infrastructure, not user-visible pages)."""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app.extensions import db, limiter

log = logging.getLogger(__name__)

bp = Blueprint("health", __name__)

# These endpoints are infra; exempt them from rate limiting and CSRF.
limiter.exempt(bp)


@bp.get("/healthz")
def healthz():  # type: ignore[no-untyped-def]
    return jsonify(status="ok"), 200


@bp.get("/readyz")
def readyz():  # type: ignore[no-untyped-def]
    checks: dict[str, str] = {}
    overall = 200
    try:
        db.session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:  # noqa: BLE001
        log.warning("readyz db check failed: %s", exc)
        checks["db"] = "down"
        overall = 503

    redis_url = current_app.config.get("RATELIMIT_STORAGE_URI", "")
    if redis_url.startswith("redis://"):
        try:
            import redis  # local import keeps health blueprint importable without redis

            r = redis.Redis.from_url(redis_url, socket_connect_timeout=1)
            r.ping()
            checks["redis"] = "ok"
        except Exception as exc:  # noqa: BLE001
            log.warning("readyz redis check failed: %s", exc)
            checks["redis"] = "down"
            overall = 503
    return jsonify(checks), overall
