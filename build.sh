#!/usr/bin/env bash
# Render Build Script — runs automatically on every deploy.
set -o errexit   # exit immediately if any command fails

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
