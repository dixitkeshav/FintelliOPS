#!/bin/sh
set -e

python manage.py migrate --noinput

if [ "$1" != "celery" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
