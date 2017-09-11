#!/bin/bash

# rodar esse script na raiz do projeto

DIR=~/logs_migracao
mkdir -p $DIR

LOG="$DIR/$1.migracao.log"
rm -f $LOG

echo "########################################" | tee -a $LOG
echo "MIGRANDO BANCO $1" | tee -a $LOG
echo "########################################" | tee -a $LOG
echo >> $LOG


echo "--- MIGRACAO DE DADOS ---" | tee -a $LOG
echo >> $LOG
DATABASE_NAME=$1 ./manage.py migracao_25_31 -f --settings sapl.legacy_migration_settings |& tee -a $LOG
echo >> $LOG
