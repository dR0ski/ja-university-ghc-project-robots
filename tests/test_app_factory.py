def test_factory_returns_app():
    from flask import Flask

    from app import create_app

    application = create_app("testing")
    assert isinstance(application, Flask)
    rules = {r.endpoint for r in application.url_map.iter_rules()}
    assert "public.splash" in rules
    assert "auth.register" in rules
    assert "auth.register_success" in rules
    assert "health.healthz" in rules
    assert "health.readyz" in rules


def test_prod_config_fails_without_secret(monkeypatch):
    import pytest

    from app.config import ProdConfig

    monkeypatch.setenv("SECRET_KEY", "short")
    with pytest.raises(RuntimeError):
        ProdConfig()
