#!/bin/bash

# rodar esse script na raiz do projeto


if [ $# -ge 1 ]; then
    # mysql com senha
    parallel -eta --verbose -j+0 ./sapl/legacy/scripts/migra_um_db.sh :::: <(mysql -u $1 -p$2 -e 'show databases;' | grep '^sapl_') ::: $1 ::: $2
elif [ $# -ge 0 ]; then
    # mysql sem senha
    parallel -eta --verbose -j+0 ./sapl/legacy/scripts/migra_um_db.sh :::: <(mysql -u $1 -e 'show databases;' | grep '^sapl_') ::: $1
else
    echo "USO:"
    echo "    $0 <usuário mysql> [senha mysql]"
fi;