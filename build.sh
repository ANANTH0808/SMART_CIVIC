#!/usr/bin/env bash
# Render Build Script — runs automatically on every deploy.
set -o errexit   # exit immediately if any command fails

pip install -r requirements.txt

python manage.py collectstatic --no-input

# ---------------------------------------------------------------------------
# Smart migration state repair.
#
# Multiple failed deploys can leave the database in a mixed state:
#   - some tables exist (their transactions committed)
#   - some tables are missing (their transactions rolled back)
#   - django_migrations may or may not have matching records
#
# Strategy:
#   1. Check which key tables actually exist in the database.
#   2. DELETE django_migrations records ONLY for apps whose tables are missing.
#      (Keeping records for tables that exist stops Django re-creating them.)
#   3. Run migrate --fake-initial as a safety net for any remaining mismatch.
# ---------------------------------------------------------------------------
python - <<'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_civic.settings')
django.setup()

from django.db import connection

# Map each Django app to one representative table that proves it was migrated.
APP_TABLE = {
    'contenttypes': 'django_content_type',
    'auth':         'auth_user',
    'admin':        'django_admin_log',
    'sessions':     'django_session',
    'complaints':   'complaints_complaint',
}

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
        missing = [app for app, tbl in APP_TABLE.items() if not table_exists(cur, tbl)]

        if not missing:
            print("All key tables exist — migration state looks healthy.")
        else:
            print(f"Missing tables for apps: {missing}")

            # If a core app (auth/contenttypes) is missing, dependent apps
            # must also be re-migrated even if their tables happen to exist.
            if 'auth' in missing or 'contenttypes' in missing:
                for dep in ('admin', 'sessions', 'complaints'):
                    if dep not in missing:
                        missing.append(dep)

            try:
                placeholders = ', '.join(['%s'] * len(missing))
                cur.execute(
                    f"DELETE FROM django_migrations WHERE app IN ({placeholders})",
                    missing,
                )
                print(f"Cleared stale records for: {missing}")
                print("Django will now re-apply those migrations cleanly.")
            except Exception as ex:
                print(f"Could not clean django_migrations (may not exist yet): {ex}")

except Exception as exc:
    print(f"Migration state check skipped: {exc}")
PYEOF

# --fake-initial: if an initial migration's tables already exist, mark it as
# applied without re-running it (handles any remaining edge-case mismatches).
python manage.py migrate --fake-initial
