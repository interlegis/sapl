#!/bin/sh

python3 gen-env.py
python3 manage.py bower install

/bin/sh busy-wait.sh

python3 manage.py migrate
python3 manage.py collectstatic --no-input
python3 manage.py rebuild_index --noinput

/bin/sh gunicorn_start.sh
