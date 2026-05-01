#!/usr/bin/env sh
set -eu

echo "[entrypoint] running migrations..."
flask --app wsgi db upgrade
echo "[entrypoint] migrations complete; starting:" "$@"
exec "$@"
