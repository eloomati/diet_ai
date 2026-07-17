#!/usr/bin/env bash
set -euo pipefail

# Optional toggles
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
DB_WAIT_TIMEOUT_SECONDS="${DB_WAIT_TIMEOUT_SECONDS:-60}"

python <<'PY'
import os
import sys
import time

import psycopg2

db_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
if not db_url:
    print("POSTGRES_URL/DATABASE_URL is not set; skipping DB wait.", flush=True)
    sys.exit(0)

# Convert SQLAlchemy URL to psycopg2 URL when needed
db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
timeout = int(os.getenv("DB_WAIT_TIMEOUT_SECONDS", "60"))
deadline = time.time() + timeout

print(f"Waiting for PostgreSQL up to {timeout}s...", flush=True)
while True:
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print("PostgreSQL is ready.", flush=True)
        break
    except Exception as exc:
        if time.time() > deadline:
            print(f"PostgreSQL wait timeout: {exc}", flush=True)
            raise
        time.sleep(1)
PY

if [ "${RUN_MIGRATIONS}" = "1" ]; then
  python <<'PY'
import os
import subprocess
import sys

import psycopg2

db_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
if not db_url:
    print("POSTGRES_URL/DATABASE_URL is not set; cannot run migrations.", flush=True)
    sys.exit(1)

db_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")

LOCK_ID = 842197  # App-specific advisory lock id

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

print("Acquiring PostgreSQL advisory lock for migrations...", flush=True)
cur.execute("SELECT pg_advisory_lock(%s);", (LOCK_ID,))

try:
    print("Running Alembic migrations...", flush=True)
    subprocess.run(
        ["alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        check=True,
    )
    print("Migrations completed.", flush=True)
finally:
    cur.execute("SELECT pg_advisory_unlock(%s);", (LOCK_ID,))
    cur.close()
    conn.close()
    print("Migration lock released.", flush=True)
PY
else
  echo "RUN_MIGRATIONS=0 -> skipping migrations"
fi

echo "[entrypoint] starting app..."
exec "$@"