#!/bin/bash

# QA checks: run this before every commit

./manage.py check
pep8 --exclude=ipython_log.py* --exclude=migrations .
