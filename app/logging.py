"""Structured logging with sensitive-field redaction and request-id binding."""

from __future__ import annotations

import logging
import sys
from typing import Any

from flask import Flask, g, has_request_context
from pythonjsonlogger import jsonlogger

REDACTED_FIELDS = frozenset(
    {"password", "password_confirm", "csrf_token", "authorization", "cookie"}
)


class RedactSensitiveFilter(logging.Filter):
    """Mask sensitive fields anywhere in the LogRecord's extras or args."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key in list(record.__dict__.keys()):
            if key.lower() in REDACTED_FIELDS:
                record.__dict__[key] = "***"
        return True


class RequestContextFilter(logging.Filter):
    """Attach request_id from flask.g to every record (when in a request)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
        else:
            record.request_id = "-"
        return True


class _JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault("request_id", getattr(record, "request_id", "-"))


def configure_logging(app: Flask) -> None:
    """Attach handlers to the root logger; called once from the factory."""
    root = logging.getLogger()
    # Clear any handlers a previous boot/test session attached.
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.addFilter(RedactSensitiveFilter())
    handler.addFilter(RequestContextFilter())

    if app.config.get("LOG_JSON", False):
        fmt = _JsonFormatter(
            "%(asctime)s %(level)s %(logger)s %(message)s %(request_id)s"
        )
    else:
        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
        )
    handler.setFormatter(fmt)
    root.addHandler(handler)
    root.setLevel(app.config.get("LOG_LEVEL", "INFO"))

    # Quiet werkzeug in non-debug.
    if not app.debug:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
