# Robotik

Production-grade Flask app for publishing robot videos and images. This milestone ships **two pages only** — a TikTok-styled marketing splash and a secure registration page — on a foundation built to scale.

Default dev stack uses **SQLite** (Python stdlib) and an **in-memory rate limiter** — no system services required. Postgres + Redis are supported in production via env vars.

## Quickstart

```bash
cp .env.example .env

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

flask --app wsgi db upgrade      # creates robotik.db (SQLite)
make dev                         # → http://localhost:8000
```

## Routes

| Path | Method | Description |
|---|---|---|
| `/` | GET | Marketing splash (hero video, features, footer) |
| `/register` | GET, POST | Registration form (CSRF, rate-limited, honeypot, no-enumeration) |
| `/register/success` | GET | Generic post-submit confirmation |
| `/healthz` | GET | Liveness — no dependencies |
| `/readyz` | GET | Readiness — checks DB (and Redis if configured) |
| `/terms`, `/privacy`, `/contact` | GET | 503 stubs |

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

All styling lives in **one file**: `app/static/css/main.css` (tokens → reset → primitives → components).

## Production with Postgres + Redis

```bash
pip install -e ".[dev,postgres]"
export DATABASE_URL="postgresql+psycopg://user:pw@host:5432/dbname"
export RATELIMIT_STORAGE_URI="redis://host:6379/0"
export SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export FLASK_ENV=production
flask --app wsgi db upgrade
gunicorn -w 4 -k gthread --threads 4 -b 0.0.0.0:8000 wsgi:app
```

`ProdConfig` refuses to boot when `SECRET_KEY` is < 32 chars or `DATABASE_URL` is missing.

## Make targets

```
make install          # create .venv and install deps
make dev              # flask debug server
make run              # gunicorn (prod-style)
make migrate          # flask db upgrade
make migration name="..."  # generate a revision
make test             # pytest with coverage gate
make lint             # ruff check + format check
make typecheck        # mypy strict on app/
make fmt              # ruff fix + format
make ci               # lint + typecheck + test
```

## Testing

The suite uses SQLite by default at `./robotik_test.db`. Set `TEST_DATABASE_URL` to point at Postgres if you want parity with prod.

## Adding a new blueprint

1. `app/blueprints/<name>/{__init__.py, routes.py}`.
2. Define `bp = Blueprint("<name>", __name__)` and at least one route.
3. Register in `app/factory.py`'s `create_app`.
4. Add tests under `tests/`.

## Security

See [SECURITY.md](SECURITY.md).
