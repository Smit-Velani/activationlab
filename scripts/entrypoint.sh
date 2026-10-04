#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

exec "$@"
