#!/usr/bin/env bash
# Render Build Script — runs automatically on every deploy.
set -o errexit   # exit immediately if any command fails

pip install -r requirements.txt

python manage.py collectstatic --no-input

# ---------------------------------------------------------------------------
# Repair inconsistent migration state.
#
# Problem: a previous failed deploy can commit rows to django_migrations for
# 'auth' and 'contenttypes' WITHOUT the actual tables existing (because the
# FK constraint step rolled back after the INSERT into django_migrations was
# already committed in a separate sub-transaction).
#
# Fix: if auth_user table is missing but django_migrations claims auth was
# applied, delete those stale records so Django re-runs the migrations.
# ---------------------------------------------------------------------------
python - <<'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_civic.settings')
django.setup()

from django.db import connection

APPS_TO_RESET = ('auth', 'contenttypes', 'admin', 'sessions', 'complaints')

def table_exists(cursor, name):
    cursor.execute(
        "SELECT EXISTS("
        "  SELECT 1 FROM information_schema.tables"
        "  WHERE table_schema = 'public' AND table_name = %s"
        ")",
        [name],
    )
    return cursor.fetchone()[0]

try:
    with connection.cursor() as cur:
        if not table_exists(cur, 'auth_user'):
            print("auth_user is missing — cleaning stale migration records ...")
            try:
                placeholders = ', '.join(['%s'] * len(APPS_TO_RESET))
                cur.execute(
                    f"DELETE FROM django_migrations WHERE app IN ({placeholders})",
                    list(APPS_TO_RESET),
                )
                print(f"Removed stale records for: {APPS_TO_RESET}")
            except Exception:
                print("django_migrations table not found — fresh database, nothing to clean.")
        else:
            print("auth_user exists — migration state is consistent, nothing to repair.")
except Exception as exc:
    print(f"Migration state check skipped: {exc}")
PYEOF

# Run all migrations (auth tables will now be created fresh if needed)
python manage.py migrate
