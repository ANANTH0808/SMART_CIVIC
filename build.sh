#!/usr/bin/env bash
# Render Build Script — runs automatically on every deploy.
set -o errexit   # exit immediately if any command fails

pip install -r requirements.txt

python manage.py collectstatic --no-input

# ---------------------------------------------------------------------------
# Database consistency check & repair.
#
# Multiple failed deploys can leave PostgreSQL in a partial state where some
# tables exist and some don't.  The only reliable recovery is a clean reset:
# drop every Django-managed table (IF EXISTS CASCADE — safe on a fresh DB too)
# so migrate runs from a true blank slate.
#
# This block ONLY triggers when auth_user is missing, which means either:
#   a) Fresh database — nothing to lose.
#   b) Partial migration state — no real users exist yet anyway.
#
# Once the app is successfully deployed once, auth_user will exist and this
# block is skipped on every future deploy. Production data is never at risk.
# ---------------------------------------------------------------------------
python - <<'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_civic.settings')
django.setup()

from django.db import connection

def table_exists(cursor, name):
    cursor.execute(
        "SELECT EXISTS("
        "  SELECT 1 FROM information_schema.tables"
        "  WHERE table_schema = 'public' AND table_name = %s"
        ")",
        [name],
    )
    return cursor.fetchone()[0]

# All tables Django creates for this project, in safe drop order
# (children before parents; CASCADE handles anything we miss).
ALL_TABLES = [
    # App tables
    'complaints_notification',
    'complaints_comment',
    'complaints_complaint',
    # Admin
    'django_admin_log',
    # Auth junction tables (must come before auth_user / auth_group)
    'auth_user_user_permissions',
    'auth_user_groups',
    'auth_group_permissions',
    # Auth core
    'auth_user',
    'auth_group',
    'auth_permission',
    # Sessions & content types
    'django_session',
    'django_content_type',
    # Migration history (last — we want a fresh run)
    'django_migrations',
]

try:
    with connection.cursor() as cur:
        if table_exists(cur, 'auth_user'):
            print("auth_user exists — database is healthy, skipping reset.")
        else:
            print("auth_user is missing — performing clean table reset ...")
            for table in ALL_TABLES:
                cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                print(f"  dropped (if existed): {table}")
            print("Clean slate ready — migrate will now build everything fresh.")
except Exception as exc:
    print(f"Reset check failed (continuing anyway): {exc}")
PYEOF

python manage.py migrate
