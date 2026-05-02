"""Error handlers — render minimal templates with request_id, no stack traces."""

from __future__ import annotations

import logging

from flask import Flask, g, render_template
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


def init_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(_e):  # type: ignore[no-untyped-def]
        return render_template("errors/400.html", request_id=getattr(g, "request_id", "-")), 400

    @app.errorhandler(403)
    def forbidden(_e):  # type: ignore[no-untyped-def]
        return render_template("errors/403.html", request_id=getattr(g, "request_id", "-")), 403

    @app.errorhandler(404)
    def not_found(_e):  # type: ignore[no-untyped-def]
        return render_template("errors/404.html", request_id=getattr(g, "request_id", "-")), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):  # type: ignore[no-untyped-def]
        return render_template("errors/404.html", request_id=getattr(g, "request_id", "-")), 404

    @app.errorhandler(413)
    def too_large(_e):  # type: ignore[no-untyped-def]
        return render_template("errors/400.html", request_id=getattr(g, "request_id", "-")), 400

    @app.errorhandler(429)
    def too_many(_e):  # type: ignore[no-untyped-def]
        retry_after = getattr(_e, "description", None)
        resp = render_template("errors/429.html", request_id=getattr(g, "request_id", "-"))
        return resp, 429, {"Retry-After": "60"} if retry_after is None else {"Retry-After": "60"}

    @app.errorhandler(500)
    def server_error(e):  # type: ignore[no-untyped-def]
        log.exception("unhandled 500", extra={"request_id": getattr(g, "request_id", "-")})
        return render_template("errors/500.html", request_id=getattr(g, "request_id", "-")), 500

    @app.errorhandler(Exception)
    def unhandled(e):  # type: ignore[no-untyped-def]
        if isinstance(e, HTTPException):
            return e
        log.exception("unhandled exception", extra={"request_id": getattr(g, "request_id", "-")})
        return render_template("errors/500.html", request_id=getattr(g, "request_id", "-")), 500
