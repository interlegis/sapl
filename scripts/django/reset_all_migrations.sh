#!/usr/bin/env bash

# Sends all django migrations to the trash bin
#   Requires trash-cli. To install:
#   sudo apt-get install trash-cli
hash trash-put 2>/dev/null || { echo >&2 "I require trash-put but it's not installed.  Aborting."; exit 1; }

git_project_root=$(git rev-parse --show-toplevel)
cd ${git_project_root}

find -name 00*.py | grep /migrations/ | xargs trash-put

# Make all migrations from scratch
./manage.py makemigrations
