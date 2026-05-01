"""Auth routes — register form (GET/POST) + post-submit success page."""

from __future__ import annotations

import logging

from flask import Blueprint, redirect, render_template, request, url_for

from app.blueprints.auth.forms import RegisterForm
from app.blueprints.auth.services import register_user
from app.extensions import limiter

log = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute;20 per hour", methods=["POST"])
def register():  # type: ignore[no-untyped-def]
    form = RegisterForm()
    if request.method == "POST":
        # Honeypot: silently treat as success without persisting.
        if form.website.data:
            log.info("honeypot triggered", extra={"path": "/register"})
            return redirect(url_for("auth.register_success"), code=303)

        if form.validate_on_submit():
            register_user(
                email=form.email.data or "",
                display_name=form.display_name.data or "",
                password=form.password.data or "",
            )
            # Always identical redirect — created vs duplicate indistinguishable.
            return redirect(url_for("auth.register_success"), code=303)

        # Validation failed — re-render with 400 so error semantics are correct.
        return render_template("auth/register.html", form=form), 400

    return render_template("auth/register.html", form=form)


@bp.get("/register/success")
def register_success():  # type: ignore[no-untyped-def]
    return render_template("auth/register_success.html")
