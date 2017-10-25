#!/bin/bash

# Verifica se um breakpoint foi esquecido no código
me=`basename "$0"`
busca=`grep --color=auto --exclude=$me --exclude=ipython_log.py* -r -l "pdb.set_trace()" .`

if [ ! -z "$busca" ]
then
    echo "============================================================================"
    echo "ERROR: pdb.set_trace() encontrado nos seguintes arquivos. Remova, por favor."
    echo "$busca"
    echo "============================================================================"
fi

# ./manage.py check
# flake8 --exclude='ipython_log.py*,migrations,templates' .
# isort --recursive --check-only --skip='migrations' --skip='templates' --skip='ipython_log.py' .
