#!/bin/bash

# QA checks: run this before every commit

./manage.py check
py.test
flake8 --exclude='ipython_log.py*,migrations' .
