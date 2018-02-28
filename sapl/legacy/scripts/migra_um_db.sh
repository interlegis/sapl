#!/bin/bash

# rodar esse script na raiz do projeto
if [ $# -ge 2 ]; then

    # proteje pasta com dumps de alterações acidentais
    chmod -R -w ~/migracao_sapl/sapl_dumps

    DATE=$(date +%Y-%m-%d)
    DIR=~/${DATE}_logs_migracao
    mkdir -p $DIR

    LOG="$DIR/$1.migracao.log"
    rm -f $LOG

    echo "########################################" | tee -a $LOG
    echo "MIGRANDO BANCO $1" | tee -a $LOG
    echo "########################################" | tee -a $LOG
    echo >> $LOG

    if [ $3 ]; then
        # se há senha do mysql
        mysql -u $2 -p "$3" -N -s -e "DROP DATABASE IF EXISTS $1; CREATE DATABASE $1;"
        mysql -u $2 -p "$3" < ~/migracao_sapl/sapl_dumps/$1.sql
    else
        # se não há senha do mysql
        mysql -u $2 -N -s -e "DROP DATABASE IF EXISTS $1; CREATE DATABASE $1;"
        mysql -u $2 < ~/migracao_sapl/sapl_dumps/$1.sql
    fi;
    echo "O banco legado foi restaurado" |& tee -a $LOG
    echo >> $LOG

    echo "--- DJANGO MIGRATE ---" | tee -a $LOG
    echo >> $LOG
    DATABASE_NAME=$1 ./manage.py migrate --settings sapl.legacy_migration_settings
    echo >> $LOG

    echo "--- MIGRACAO DE DADOS ---" | tee -a $LOG
    echo >> $LOG
    DATABASE_NAME=$1 ./manage.py migracao_25_31 -f --settings sapl.legacy_migration_settings |& tee -a $LOG
    echo >> $LOG
else
    echo "USO:"
    echo "    $0 <nome_database> <usuário mysql> [senha mysql]"
fi;
