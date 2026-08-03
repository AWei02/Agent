#!/bin/sh
set -eu

export PGPASSWORD="$POSTGRES_PASSWORD"

if psql -h postgres -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'langfuse'" | grep -q 1; then
  exit 0
fi

psql -h postgres -U postgres -d postgres -c 'CREATE DATABASE langfuse;'
