"""User model — argon2id passwords. Portable across SQLite (dev) and Postgres (prod)."""

from __future__ import annotations

import uuid
from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from email_validator import EmailNotValidError, validate_email
from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import TimestampMixin

_ph = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


class User(TimestampMixin, db.Model):  # type: ignore[name-defined,misc]
    __tablename__ = "users"

    # UUID stored as 36-char string for portability (SQLite + Postgres).
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Email stored lowercased; normalization happens in the service layer.
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("length(email) <= 254", name="users_email_len_chk"),
        CheckConstraint(
            "display_name IS NULL OR length(display_name) <= 64",
            name="users_display_name_len_chk",
        ),
        Index("ix_users_created_at", "created_at"),
    )

    def set_password(self, plaintext: str) -> None:
        if not (12 <= len(plaintext) <= 128):
            raise ValueError("password length out of range")
        self.password_hash = _ph.hash(plaintext)

    def check_password(self, plaintext: str) -> bool:
        if not self.password_hash:
            return False
        try:
            _ph.verify(self.password_hash, plaintext)
        except VerifyMismatchError:
            return False
        if _ph.check_needs_rehash(self.password_hash):
            self.password_hash = _ph.hash(plaintext)
        return True

    @staticmethod
    def normalize_email(raw: str) -> str:
        try:
            v = validate_email(raw, check_deliverability=False)
        except EmailNotValidError as exc:
            raise ValueError(str(exc)) from exc
        return v.normalized.lower()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r} verified={self.is_verified}>"
