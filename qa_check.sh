#!/bin/bash

# QA checks: run this before every commit

./manage.py check
flake8 --exclude='ipython_log.py*,migrations' .
isort --check-only --skip='migrations' --skip='ipython_log.py' -rc .
