#!/usr/bin/env bash
set -o errexit

# Render build — run from backend/ (rootDir)
cd "$(dirname "$0")"

pip install --upgrade pip
pip install -r ../requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
