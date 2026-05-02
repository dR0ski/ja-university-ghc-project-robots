.PHONY: venv install db-create db-drop migrate migration dev run test lint typecheck fmt shell psql services-start services-stop ci bootstrap

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
FLASK := $(VENV)/bin/flask
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
GUNICORN := $(VENV)/bin/gunicorn

PG_USER ?= robot
PG_DB   ?= robot

# ----- Python env -----
$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -U pip

venv: $(VENV)/bin/activate

install: venv
	$(PIP) install -e ".[dev]"

# ----- Local services (Homebrew) -----
services-start:
	brew services start postgresql@16 || brew services start postgresql
	brew services start redis

services-stop:
	brew services stop postgresql@16 || brew services stop postgresql
	brew services stop redis

# ----- Database -----
db-create:
	createuser -s $(PG_USER) 2>/dev/null || true
	createdb -O $(PG_USER) $(PG_DB) 2>/dev/null || true
	psql -d $(PG_DB) -c "CREATE EXTENSION IF NOT EXISTS citext; CREATE EXTENSION IF NOT EXISTS pgcrypto;"

db-drop:
	dropdb $(PG_DB) 2>/dev/null || true

migrate:
	$(FLASK) --app wsgi db upgrade

migration:
	@if [ -z "$(name)" ]; then echo "usage: make migration name=<message>"; exit 1; fi
	$(FLASK) --app wsgi db migrate -m "$(name)"

# ----- Run -----
dev:
	FLASK_ENV=development $(FLASK) --app wsgi run --host 0.0.0.0 --port 8000 --debug

run:
	FLASK_ENV=production $(GUNICORN) -w 2 -k gthread --threads 4 -b 0.0.0.0:8000 wsgi:app

# ----- Quality -----
test:
	$(PYTEST)

lint:
	$(RUFF) check .
	$(RUFF) format --check .

typecheck:
	$(MYPY)

fmt:
	$(RUFF) check --fix .
	$(RUFF) format .

shell:
	$(FLASK) --app wsgi shell

psql:
	psql -d $(PG_DB)

ci: lint typecheck test

# ----- One-shot bootstrap -----
bootstrap: install services-start db-create migrate
	@echo "Bootstrap complete. Run: make dev"
