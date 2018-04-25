#!/bin/bash

# rodar esse script na raiz do projeto
if [ $# -eq 1 ]; then

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

    echo "--- MIGRACAO ---" | tee -a $LOG
    echo >> $LOG
    DATABASE_NAME=$1 ./manage.py migracao_25_31 --settings sapl.legacy_migration_settings 2>&1 | tee -a $LOG
    echo >> $LOG
else
    echo "USO:"
    echo "    $0 <nome_database>"
fi;
