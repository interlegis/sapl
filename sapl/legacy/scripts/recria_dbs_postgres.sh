#!/bin/bash

# (Re)cria todos os bancos postgres para migração
# cria um banco postgres (de mesmo nome) para cada banco mysql cujo nome começa com "sapl_"

if [ $# -eq 2 ]; then
    parallel --verbose -j+0 ./recria_um_db_postgres.sh :::: <(mysql -u $1 -p$2 -e 'show databases;' | grep '^sapl_' | grep -v '_copy$')
else
    echo "USO:"
    echo "    $0 [usuário mysql] [senha mysql]"
fi;