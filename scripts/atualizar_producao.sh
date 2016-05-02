#!/bin/bash
git pull --rebase
workon sapl
pip install -r requirements/dev-requirements.txt
./manage.py migrate
./manage.py bower install
./manage.py collectstatic --noinput
deactivate
sudo supervisorctl restart sapl
