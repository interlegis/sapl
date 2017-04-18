#!/bin/sh

python3 gen-env.py
python3 manage.py bower install
/bin/sh busy-wait.sh
python3 manage.py migrate
/bin/sh gunicorn_start.sh
