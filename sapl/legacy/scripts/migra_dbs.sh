#!/bin/bash

# rodar esse script na raiz do projeto

if [ $# -eq 2 ]; then
    parallel -eta --verbose ./sapl/legacy/scripts/migra_um_db.sh :::: <(mysql -u $1 -p$2 -e 'show databases;' | grep '^sapl_' | grep -v '_copy$') ::: $1 ::: $2
else
    echo "USO:"
    echo "    ./sapl/legacy/scripts/migra_dbs.sh [usuário mysql] [senha mysql]"
fi;

