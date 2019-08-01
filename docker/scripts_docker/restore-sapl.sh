#!/bin/bash


###
### NÃO ESTÁ RESTAURANDO CORRETAMENTE O BANCO!!!!
###

BACKUP_DIR=$1
if [ -z $BACKUP_DIR ]; then
   echo "Diretório de backup não informado!"
   echo "uso: $./restore-sapl.sh <backup directory>"
   exit 1
fi

# RESTORE DO BANCO DE DADOS
sudo docker cp ./$BACKUP_DIR/database.backup postgres:/tmp/
sudo docker exec -it postgres bash -c 'ls -lah /tmp/database.backup'

# --clean --data-only --disable-trigger ????
sudo docker exec -it postgres bash -c 'pg_restore --disable-triggers --data-only -Fc -v -U sapl -d sapl  /tmp/database.backup'

# RESTORE DA PASTA MEDIA
sudo docker cp ./$BACKUP_DIR/media.tar.gz sapl:/var/interlegis/sapl
sudo docker exec -it sapl bash -c 'ls -lah /var/interlegis/sapl/media.tar.gz'
#sudo docker exec -it sapl bash -c 'cd /var/interlegis/sapl && tar -zxvf media.tar.gz .'

