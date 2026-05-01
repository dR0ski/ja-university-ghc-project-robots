"""Application factory."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import BaseConfig, get_config
from app.context_processors import init_context_processors
from app.error_handlers import init_error_handlers
from app.extensions import csrf, db, limiter, migrate
from app.health import bp as health_bp
from app.logging import configure_logging
from app.middleware.request_id import init_request_id
from app.security import init_security

log = logging.getLogger(__name__)


def _compute_asset_hash(app: Flask) -> str:
    """Hash the global stylesheet so templates can cache-bust on deploy."""
    css_path = Path(app.static_folder or "app/static") / "css" / "main.css"
    try:
        data = css_path.read_bytes()
        return hashlib.sha256(data).hexdigest()[:12]
    except OSError:
        return "dev"


def _maybe_init_sentry(app: Flask) -> None:
    dsn = app.config.get("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        def _scrub(event, _hint):  # type: ignore[no-untyped-def]
            req = event.get("request") or {}
            data = req.get("data")
            if isinstance(data, dict):
                for k in list(data.keys()):
                    if k.lower() in {"password", "password_confirm", "csrf_token"}:
                        data[k] = "***"
            return event

        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            release=app.config.get("RELEASE") or None,
            before_send=_scrub,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Sentry init skipped: %s", exc)


def create_app(config_name: str | None = None) -> Flask:
    """Build and configure a Flask application instance."""
    # Load .env only outside production (prod uses real env / secret manager).
    if (config_name or os.environ.get("FLASK_ENV", "production")) != "production":
        load_dotenv(override=False)

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    cfg: BaseConfig = get_config(config_name)
    app.config.from_object(cfg)
    # config.from_object copies class attributes; ensure instance attrs (ProdConfig __init__) too.
    for k in dir(cfg):
        if k.isupper():
            app.config[k] = getattr(cfg, k)

    app.config["ASSET_HASH"] = _compute_asset_hash(app)

    # Logging first so subsequent boot messages are captured.
    configure_logging(app)

    # ProxyFix when running behind a load balancer.
    proxies = int(app.config.get("TRUSTED_PROXY_COUNT", 0) or 0)
    if proxies > 0:
        app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
            app.wsgi_app, x_for=proxies, x_proto=proxies, x_host=proxies, x_prefix=proxies
        )

    # Request ID before extensions so logs during init can carry it (no-op pre-request).
    init_request_id(app)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    # Security headers (Talisman + custom)
    init_security(app)

    # Blueprints
    from app.blueprints.auth.routes import bp as auth_bp
    from app.blueprints.public.routes import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)

    # CSRF exempt infra endpoints
    csrf.exempt(health_bp)

    # Error handlers + context processors
    init_error_handlers(app)
    init_context_processors(app)

    # Optional Sentry
    _maybe_init_sentry(app)

    log.info(
        "app booted",
        extra={
            "env": type(cfg).__name__,
            "force_https": app.config.get("FORCE_HTTPS"),
            "asset_hash": app.config["ASSET_HASH"],
        },
    )
    return app
