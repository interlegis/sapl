#!/bin/bash

# QA checks: run this before every commit

./manage.py check
flake8 --exclude='ipython_log.py*,migrations,templates' .
isort --recursive --check-only --skip='migrations' --skip='templates' --skip='ipython_log.py' .
