#!/bin/bash
git pull
pip install -r requirements/dev-requirements.txt
./manage.py migrate
./manage.py bower install
./manage.py collectstatic --noinput
sudo supervisorctl restart sapl
