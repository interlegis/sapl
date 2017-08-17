#!/bin/bash

python manage.py makemigrations --dry-run --exit > /dev/null

MIGRATIONS=$?

[ $MIGRATIONS -eq 0 ] && echo "You have unapplied code change. run 'python manage.py makemigrations'" && exit 1
[ $MIGRATIONS -ne 0 ] && echo "" && exit 0