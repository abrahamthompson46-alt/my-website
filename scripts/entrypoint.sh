#!/bin/sh
set -e

echo "Waiting for database..."
python <<'PY'
import os, sys, time
import psycopg

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))
user = os.environ.get("DB_USER", "postgres")
password = os.environ.get("DB_PASSWORD", "")
dbname = os.environ.get("DB_NAME", "enterprise_platform")

for attempt in range(30):
    try:
        with psycopg.connect(host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=3):
            print("Database is ready.")
            sys.exit(0)
    except Exception as exc:
        print(f"Database not ready ({attempt + 1}/30): {exc}")
        time.sleep(2)

print("Database connection timed out.")
sys.exit(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
