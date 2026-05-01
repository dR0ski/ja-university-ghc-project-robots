.PHONY: install dev run test lint typecheck fmt migrate migration shell psql compose-up compose-down ci

install:
	python -m pip install -U pip
	pip install -e ".[dev]"

dev:
	FLASK_ENV=development flask --app wsgi run --host 0.0.0.0 --port 8000 --debug

run:
	gunicorn -c gunicorn.conf.py wsgi:app

test:
	pytest

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy

fmt:
	ruff check --fix .
	ruff format .

migrate:
	flask --app wsgi db upgrade

migration:
	@if [ -z "$(name)" ]; then echo "usage: make migration name=<message>"; exit 1; fi
	flask --app wsgi db migrate -m "$(name)"

shell:
	flask --app wsgi shell

psql:
	docker compose exec db psql -U $${POSTGRES_USER:-robot} -d $${POSTGRES_DB:-robot}

compose-up:
	docker compose up --build

compose-down:
	docker compose down -v

ci: lint typecheck test
