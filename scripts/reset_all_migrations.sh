#!/bin/bash

# Sends all django migrations to the trash bin
#   Requires trash-cli. To install:
#   sudo apt-get install trash-cli
find -name 00*.py | grep /migrations/ | xargs trash-put

# Make all migrations from scratch
./manage.py makemigrations
