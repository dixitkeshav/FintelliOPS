#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
  npx prisma migrate deploy
fi

exec npm start -- -H 0.0.0.0 -p 3000
