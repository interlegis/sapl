#!/bin/bash

# rodar esse script na raiz do projeto

if [ $# -eq 2 ]; then
    parallel -eta --verbose -j+0 ./sapl/legacy/scripts/migra_um_db.sh :::: <(mysql -u $1 -p$2 -e 'show databases;' | grep '^sapl_' | grep -v '_copy$') ::: $1 ::: $2
else
    echo "USO:"
    echo "    $0 [usuário mysql] [senha mysql]"
fi;