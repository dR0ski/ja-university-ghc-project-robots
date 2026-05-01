"""Public marketing routes."""

from __future__ import annotations

from flask import Blueprint, abort, render_template

bp = Blueprint("public", __name__)


@bp.get("/")
def splash():  # type: ignore[no-untyped-def]
    return render_template("public/splash.html")


# Legal stubs — present so footer links don't 404, but render a placeholder.
@bp.get("/terms")
@bp.get("/privacy")
@bp.get("/contact")
def legal_stub():  # type: ignore[no-untyped-def]
    abort(503)
