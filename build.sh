#!/usr/bin/env bash
# Render Build Script — runs automatically on every deploy.
set -o errexit   # exit immediately if any command fails

pip install -r requirements.txt

python manage.py collectstatic --no-input

# Run auth/contenttypes first to guarantee auth_user exists before
# complaints migrations try to add FK constraints that reference it.
python manage.py migrate contenttypes
python manage.py migrate auth
python manage.py migrate
