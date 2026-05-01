# Robotik

Production-grade Flask app for publishing robot videos and images. This milestone ships **two pages only** — a TikTok-styled marketing splash and a secure registration page — on a foundation built to scale.

## Quickstart

```bash
cp .env.example .env
docker compose up --build
# → http://localhost:8000
```

The `web` container runs migrations on boot, then starts the dev Flask server (with `docker-compose.override.yml` applied automatically).

## Local (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export FLASK_ENV=development
export DATABASE_URL=postgresql+psycopg://robot:robot@localhost:5432/robot
flask --app wsgi db upgrade
make dev
```

## Routes

| Path | Method | Description |
|---|---|---|
| `/` | GET | Marketing splash (hero video, features, footer) |
| `/register` | GET, POST | Registration form (CSRF, rate-limited, honeypot, no-enumeration) |
| `/register/success` | GET | Generic post-submit confirmation |
| `/healthz` | GET | Liveness — no dependencies |
| `/readyz` | GET | Readiness — checks Postgres + Redis |
| `/terms`, `/privacy`, `/contact` | GET | 503 stubs (real copy required before launch) |

## Architecture

```
wsgi.py ──► app.create_app()
              ├── config: Dev/Test/Prod (prod fail-fast on secrets)
              ├── extensions: db, migrate, csrf, limiter, talisman
              ├── middleware: ProxyFix, request-id
              ├── security: strict CSP, HSTS, hardened cookies
              ├── blueprints: public, auth, health
              ├── error handlers: 400/403/404/413/429/500
              └── context processors: site_meta, asset_hash
```

All styling lives in **one file**: `app/static/css/main.css` (tokens → reset → primitives → components). No utility framework, no inline styles.

## Environment variables

See `.env.example`. Production-required vars are marked.

## Make targets

```
make install     # install runtime + dev deps
make dev         # flask debug server
make run         # gunicorn (prod-style)
make test        # pytest with coverage gate
make lint        # ruff + format check
make typecheck   # mypy strict on app/
make migrate     # flask db upgrade
make migration name="..."  # generate revision
make compose-up  # docker compose up --build
make ci          # lint + typecheck + test
```

## Adding a new blueprint

1. `app/blueprints/<name>/{__init__.py, routes.py}`.
2. Define `bp = Blueprint("<name>", __name__)` and at least one route.
3. Register in `app/factory.py`'s `create_app`.
4. Add tests under `tests/`.

## Verification

- `make ci` — lint, typecheck, tests with ≥ 90% coverage.
- `docker compose up --build` — both services healthy; visit `/healthz` and `/readyz`.
- `curl -I http://localhost:8000/` — verify CSP, X-Content-Type-Options, Referrer-Policy, no `Server` header.
- Lighthouse on `/` should score ≥ 90 across Perf/A11y/Best-Practices/SEO once a real hero video is in place.

## Security

See [SECURITY.md](SECURITY.md).
