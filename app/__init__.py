"""Robot media app package.

Keep package import side effects minimal. Flask and tests import `create_app`
from `app`, so we expose a small lazy wrapper instead of importing the full
factory module at package import time.
"""

from __future__ import annotations

from flask import Flask


def create_app(config_name: str | None = None) -> Flask:
	from app.factory import create_app as _create_app

	return _create_app(config_name)


__all__ = ["create_app"]
