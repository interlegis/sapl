#!/bin/bash

# rodar esse script na raiz do projeto
if [ $# -eq 3 ]; then
    DIR=~/logs_migracao
    mkdir -p $DIR

    LOG="$DIR/$1.migracao.log"
    rm -f $LOG

    echo "########################################" | tee -a $LOG
    echo "MIGRANDO BANCO $1" | tee -a $LOG
    echo "########################################" | tee -a $LOG
    echo >> $LOG

    echo "--- CRIANDO BACKUP ---" | tee -a $LOG
    echo >> $LOG
    mysql -u $2 -p$3 -e "create database if not exists $1_copy;" && mysqldump -u $2 -p$3 $1 | mysql -u $2 -p$3 $1_copy;
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
    echo "    ./sapl/legacy/scripts/migra_um_db.sh [nome_database] [usuário mysql] [senha mysql]"
fi;
