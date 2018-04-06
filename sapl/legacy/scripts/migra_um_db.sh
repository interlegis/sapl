#!/bin/bash

# rodar esse script na raiz do projeto
if [ $# -ge 2 ]; then

    # proteje pasta com dumps de alterações acidentais
    # chmod -R -w ~/migracao_sapl/sapl_dumps

    DIR_MIGRACAO=~/migracao_sapl

    DATE=$(date +%Y-%m-%d)
    DIR_LOGS=$DIR_MIGRACAO/logs/$DATE
    mkdir -p $DIR_LOGS

    LOG="$DIR_LOGS/$1.migracao.log"
    rm -f $LOG

    echo "########################################" | tee -a $LOG
    echo "MIGRANDO BANCO $1" | tee -a $LOG
    echo "########################################" | tee -a $LOG
    echo >> $LOG

    if [ $3 ]; then
        # se há senha do mysql
        mysql -u$2 -p"$3" -N -s -e "DROP DATABASE IF EXISTS $1; CREATE DATABASE $1;"
        mysql -u$2 -p"$3" < $DIR_MIGRACAO/dumps_mysql/$1.sql
    else
        # se não há senha do mysql
        mysql -u$2 -N -s -e "DROP DATABASE IF EXISTS $1; CREATE DATABASE $1;"
        mysql -u$2 < $DIR_MIGRACAO/dumps_mysql/$1.sql
    fi;
    echo "O banco legado foi restaurado" |& tee -a $LOG
    echo >> $LOG

    echo "--- DJANGO MIGRATE ---" | tee -a $LOG
    echo >> $LOG
    DATABASE_NAME=$1 ./manage.py migrate --settings sapl.legacy_migration_settings
    echo >> $LOG

    echo "--- MIGRACAO ---" | tee -a $LOG
    echo >> $LOG
    DATABASE_NAME=$1 ./manage.py migracao_25_31 --force --dados --settings sapl.legacy_migration_settings 2>&1 | tee -a $LOG
    echo >> $LOG
else
    echo "USO:"
    echo "    $0 <nome_database> <usuário mysql> [senha mysql]"
fi;
