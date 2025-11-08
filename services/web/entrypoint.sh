#!/bin/sh

if [ ! -z "$@" ]; then
  exec "$@"
else
  # Use Gunicorn to serve the app
  exec gunicorn --bind 0.0.0.0:8080 project.wsgi:app --workers 4 --threads 2
fi