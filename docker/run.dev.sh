#!/bin/sh

echo "Waiting for database ..."
while ! pg_isready -h $DB_HOST -p $DB_PORT 2>/dev/null; do
    sleep 1
done

echo "Creating cache table ..."
python3 manage.py createcachetable

echo "Starting debug server with live reload ..."
exec python3 manage.py runserver 0.0.0.0:8000
