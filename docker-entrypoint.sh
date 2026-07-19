#!/bin/sh
set -eu

DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
DB_NAME="${POSTGRES_DB:-online-shop}"
export POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"

service postgresql start

if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'\"" | grep -q 1; then
    su postgres -c "createuser --login --createdb \"${DB_USER}\""
fi
su postgres -c "psql -c \"ALTER ROLE \\\"${DB_USER}\\\" WITH PASSWORD '${DB_PASSWORD}';\""

if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'\"" | grep -q 1; then
    su postgres -c "createdb --owner=\"${DB_USER}\" \"${DB_NAME}\""
fi

exec uvicorn main:app --host 0.0.0.0 --port "${FASTAPI_PORT:-3000}"
