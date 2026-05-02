"""Request-ID middleware: validates incoming X-Request-ID, else generates UUID4."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from flask import Flask, g, request


def _is_valid_uuid4(value: str) -> bool:
    try:
        u = uuid.UUID(value)
        return u.version == 4
    except (ValueError, AttributeError, TypeError):
        return False


def init_request_id(app: Flask) -> None:
    @app.before_request
    def _attach_request_id() -> None:
        incoming = request.headers.get("X-Request-ID", "")
        g.request_id = incoming if _is_valid_uuid4(incoming) else str(uuid.uuid4())

    @app.after_request
    def _emit_request_id(response: Any) -> Any:
        rid = getattr(g, "request_id", None)
        if rid:
            response.headers["X-Request-ID"] = rid
        return response


__all__: list[str] = ["init_request_id"]


# Keep a typed re-export to satisfy mypy when imported as a value.
_callable: Callable[[Flask], None] = init_request_id
