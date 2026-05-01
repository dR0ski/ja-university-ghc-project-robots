"""Auth use-cases. Thin service layer kept distinct from view code."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User

log = logging.getLogger(__name__)

RegistrationStatus = Literal["created", "duplicate", "invalid"]


@dataclass(frozen=True)
class RegistrationResult:
    status: RegistrationStatus
    user_id: str | None = None


def _hashed_id(email: str) -> str:
    return hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]


def register_user(email: str, display_name: str, password: str) -> RegistrationResult:
    """Persist a new user. Duplicates are returned as a separate status — the caller
    must treat them identically to success at the HTTP layer to prevent enumeration.
    """
    try:
        normalized = User.normalize_email(email)
    except ValueError:
        return RegistrationResult(status="invalid")

    user = User(email=normalized, display_name=display_name.strip())
    try:
        user.set_password(password)
    except ValueError:
        return RegistrationResult(status="invalid")

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        log.info(
            "duplicate registration attempt",
            extra={"email_hash": _hashed_id(normalized)},
        )
        return RegistrationResult(status="duplicate")

    log.info("user registered", extra={"email_hash": _hashed_id(normalized)})
    return RegistrationResult(status="created", user_id=str(user.id))
