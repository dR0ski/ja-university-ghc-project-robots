"""Auth forms (registration only for this milestone)."""

from __future__ import annotations

import re
from typing import Any

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
)

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
_CLASS_CHECKS = (
    re.compile(r"[a-z]"),
    re.compile(r"[A-Z]"),
    re.compile(r"\d"),
    re.compile(r"[^A-Za-z0-9]"),
)


class NoControlChars:
    """Reject control characters in free-text fields."""

    def __init__(self, message: str | None = None) -> None:
        self.message = message or "Invalid characters."

    def __call__(self, form: FlaskForm, field: Any) -> None:
        if field.data and _CONTROL_CHAR_RE.search(field.data):
            raise ValidationError(self.message)


class StrongPassword:
    """Require ≥3 of {lower, upper, digit, symbol}; reject if it equals or contains the
    email local-part or display name (case-insensitive). Never logs the value.
    """

    def __init__(self, min_classes: int = 3) -> None:
        self.min_classes = min_classes

    def __call__(self, form: FlaskForm, field: Any) -> None:
        value: str = field.data or ""
        classes = sum(1 for r in _CLASS_CHECKS if r.search(value))
        if classes < self.min_classes:
            raise ValidationError(
                "Password must include at least 3 of: lowercase, uppercase, digit, symbol."
            )
        lowered = value.lower()
        email = (getattr(form, "email", None).data or "") if hasattr(form, "email") else ""
        local = email.split("@", 1)[0].lower() if "@" in email else email.lower()
        display = (
            (getattr(form, "display_name", None).data or "")
            if hasattr(form, "display_name")
            else ""
        ).lower()
        if local and len(local) >= 4 and local in lowered:
            raise ValidationError("Password must not contain your email.")
        if display and len(display) >= 4 and display in lowered:
            raise ValidationError("Password must not contain your display name.")


class RegisterForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(check_deliverability=False), Length(max=254)],
        render_kw={
            "type": "email",
            "autocomplete": "email",
            "inputmode": "email",
            "spellcheck": "false",
            "maxlength": "254",
            "required": True,
        },
    )
    display_name = StringField(
        "Display name",
        validators=[DataRequired(), Length(min=2, max=64), NoControlChars()],
        render_kw={"autocomplete": "nickname", "maxlength": "64", "required": True},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=12, max=128), StrongPassword()],
        render_kw={
            "autocomplete": "new-password",
            "minlength": "12",
            "maxlength": "128",
            "required": True,
        },
    )
    password_confirm = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
        render_kw={"autocomplete": "new-password", "required": True},
    )
    accept_terms = BooleanField(
        "I accept the Terms and Privacy Policy.",
        validators=[DataRequired(message="You must accept the Terms.")],
    )
    # Honeypot — must remain empty. No validators; route checks manually.
    website = StringField("Leave this empty", render_kw={"tabindex": "-1", "autocomplete": "off"})
