"""Application configuration.

Production refuses to boot if required secrets are missing or weak.
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class BaseConfig:
    """Defaults shared by every environment."""

    # --- Core ---
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-not-secret")
    PREFERRED_URL_SCHEME: str = "https"

    # --- Database ---
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://robot:robot@db:5432/robot"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict[str, Any] = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    }

    # --- Sessions / cookies ---
    SESSION_COOKIE_NAME: str = "session"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = False
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(hours=12)

    # --- CSRF ---
    WTF_CSRF_TIME_LIMIT: int = 3600
    WTF_CSRF_SSL_STRICT: bool = False

    # --- Request limits ---
    MAX_CONTENT_LENGTH: int = 1 * 1024 * 1024  # 1 MB

    # --- Rate limiter ---
    RATELIMIT_STORAGE_URI: str = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_STRATEGY: str = "fixed-window-elastic-expiry"
    RATELIMIT_HEADERS_ENABLED: bool = True
    RATELIMIT_DEFAULT: str = "200 per hour;50 per minute"

    # --- Proxy ---
    TRUSTED_PROXY_COUNT: int = _env_int("TRUSTED_PROXY_COUNT", 0)

    # --- Logging ---
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_JSON: bool = _env_bool("LOG_JSON", False)

    # --- Observability ---
    SENTRY_DSN: str = os.environ.get("SENTRY_DSN", "")
    RELEASE: str = os.environ.get("RELEASE", "")

    # --- Feature flags ---
    HIBP_ENABLED: bool = _env_bool("HIBP_ENABLED", False)

    # --- Talisman / security ---
    FORCE_HTTPS: bool = False

    # Set at runtime by factory; used for static asset cache busting.
    ASSET_HASH: str = "dev"

    TESTING: bool = False
    DEBUG: bool = False


class DevConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False
    FORCE_HTTPS = False
    LOG_JSON = False


class TestConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "testing-secret-key-which-is-long-enough-yes-it-is"  # noqa: S105
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_DEFAULT = "1000 per hour"
    LOG_JSON = False


class ProdConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_NAME = "__Host-session"
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    FORCE_HTTPS = True
    LOG_JSON = True

    def __init__(self) -> None:
        # Fail-fast on missing/weak secrets.
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            raise RuntimeError(
                "ProdConfig requires SECRET_KEY of at least 32 characters; refusing to boot."
            )
        if not self.SQLALCHEMY_DATABASE_URI or "://" not in self.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("ProdConfig requires DATABASE_URL; refusing to boot.")
        if self.RATELIMIT_STORAGE_URI.startswith("memory://"):
            raise RuntimeError(
                "ProdConfig refuses memory:// rate-limit storage; set RATELIMIT_STORAGE_URI."
            )


_CONFIGS: dict[str, type[BaseConfig]] = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
}


def get_config(name: str | None = None) -> BaseConfig:
    """Resolve a config by name (defaults to FLASK_ENV, then 'production')."""
    key = (name or os.environ.get("FLASK_ENV") or "production").lower()
    cls = _CONFIGS.get(key, ProdConfig)
    return cls()
