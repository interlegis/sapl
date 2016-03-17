#!/bin/bash

# Check if there's some debug breakpoint in codebase
me=`basename "$0"`
stmts=`grep --exclude=$me -r -l "ipdb.set_trace()" * | wc -l`
if [ $stmts != '0' ]
then
    echo "=================================================================="
    echo "ERROR: ipdb.set_trace() call in codebase! Remove, please."
    grep --exclude=$me -r -n "ipdb.set_trace()" *
    echo "=================================================================="
fi

# QA checks: run this before every commit
./manage.py check
flake8 --exclude='ipython_log.py*,migrations,templates' .
isort --recursive --check-only --skip='migrations' --skip='templates' --skip='ipython_log.py' .
