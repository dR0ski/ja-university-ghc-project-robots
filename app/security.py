"""Talisman / security-header configuration.

Strict CSP: no inline styles or scripts are emitted by templates, so we never
need 'unsafe-inline' or nonces.
"""

from __future__ import annotations

from flask import Flask

from app.extensions import talisman

CSP: dict[str, list[str] | str] = {
    "default-src": "'self'",
    "base-uri": "'self'",
    "form-action": "'self'",
    "frame-ancestors": "'none'",
    "img-src": ["'self'", "data:"],
    "media-src": "'self'",
    "font-src": "'self'",
    "style-src": "'self'",
    "script-src": "'self'",
    "connect-src": "'self'",
    "object-src": "'none'",
    "manifest-src": "'self'",
}

PERMISSIONS_POLICY: dict[str, str] = {
    "accelerometer": "()",
    "camera": "()",
    "geolocation": "()",
    "gyroscope": "()",
    "microphone": "()",
    "payment": "()",
    "usb": "()",
}


def init_security(app: Flask) -> None:
    talisman.init_app(
        app,
        force_https=app.config.get("FORCE_HTTPS", False),
        strict_transport_security=app.config.get("FORCE_HTTPS", False),
        strict_transport_security_max_age=63072000,
        strict_transport_security_include_subdomains=True,
        strict_transport_security_preload=True,
        content_security_policy=CSP,
        content_security_policy_nonce_in=[],
        referrer_policy="strict-origin-when-cross-origin",
        frame_options="DENY",
        permissions_policy=PERMISSIONS_POLICY,
        session_cookie_secure=app.config.get("SESSION_COOKIE_SECURE", False),
        session_cookie_http_only=True,
    )

    @app.after_request
    def _strip_server_header(response):  # type: ignore[no-untyped-def]
        response.headers.pop("Server", None)
        # upgrade-insecure-requests is added separately because Talisman's dict form
        # does not include it by default.
        if app.config.get("FORCE_HTTPS", False):
            csp = response.headers.get("Content-Security-Policy", "")
            if "upgrade-insecure-requests" not in csp:
                response.headers["Content-Security-Policy"] = (
                    csp + "; upgrade-insecure-requests"
                ).strip("; ")
        return response
