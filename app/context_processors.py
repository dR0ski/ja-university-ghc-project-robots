"""Jinja context processors: site metadata exposed to every template."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from flask import Flask


def init_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_site_meta() -> dict[str, Any]:
        return {
            "site_name": "Robotik",
            "site_tagline": "Publish your robot. Capture the world.",
            "current_year": datetime.now(UTC).year,
            "asset_hash": app.config.get("ASSET_HASH", "dev"),
            "og_default_image": "img/og-default.png",
        }
