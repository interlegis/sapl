#!/bin/bash

# rodar esse script na raiz do projeto
if [ $# -eq 3 ]; then
    DATE=$(date +%Y-%m-%d)
    DIR=~/${DATE}_logs_migracao
    mkdir -p $DIR

    LOG="$DIR/$1.migracao.log"
    rm -f $LOG

    echo "########################################" | tee -a $LOG
    echo "MIGRANDO BANCO $1" | tee -a $LOG
    echo "########################################" | tee -a $LOG
    echo >> $LOG

    echo "--- CRIANDO BACKUP ---" | tee -a $LOG
    echo >> $LOG
    EXISTE=`mysql -u $2 -p$3 -N -s -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '$1_copy';"`

    if [[ $EXISTE == $1_copy ]]; then
		mysql -u $2 -p$3 -N -s -e "DROP DATABASE IF EXISTS $1; CREATE DATABASE $1;" && mysqldump -u $2 -p$3 $1_copy | mysql -u $2 -p$3  $1
		echo "O banco legado foi restaurado" |& tee -a $LOG
    elif [[ ! $EXISTE ]]; then
        mysql -u $2 -p$3 -N -s -e "CREATE DATABASE $1_copy;"
        mysqldump -u $2 -p$3 $1 | mysql -u $2 -p$3  $1_copy
        echo "O banco de cópia $1_copy não existia e foi criado" |& tee -a $LOG
    fi
    echo >> $LOG

    echo "--- DJANGO MIGRATE ---" | tee -a $LOG
    echo >> $LOG
    DATABASE_NAME=$1 ./manage.py migrate --settings sapl.legacy_migration_settings
    echo >> $LOG

    # XXX Na primeira execução desse comando aparece o erro de "Coammands out of sync"
    # A solução mais rápida foi executar duas vezes seguidas pra poder migrar.
    DATABASE_NAME=$1 ./manage.py migracao_25_31 -f --settings sapl.legacy_migration_settings
    echo "--- MIGRACAO DE DADOS ---" | tee -a $LOG
    echo >> $LOG
    DATABASE_NAME=$1 ./manage.py migracao_25_31 -f --settings sapl.legacy_migration_settings |& tee -a $LOG
    echo >> $LOG
else
    echo "USO:"
    echo "    $0 [nome_database] [usuário mysql] [senha mysql]"
fi;
