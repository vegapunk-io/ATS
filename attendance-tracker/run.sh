#!/usr/bin/env bash
# Convenience launcher: seed if needed, then start the server.
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit SECRET_KEY before production."
fi

python -m scripts.seed || true
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" "$@"
