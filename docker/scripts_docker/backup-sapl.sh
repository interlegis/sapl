#!/bin/bash

###
### NÃO ESTÁ BACKUP E RESTAURANDO CORRETAMENTE O BANCO!!!!
###


BACKUP_DIR=sapl-backup-`date -u +%Y-%m-%d-%H-%M`
mkdir -p ./$BACKUP_DIR

# BACKUP DO BANCO DE DADOS
sudo docker exec -it postgres bash -c 'pg_dump -U sapl -d sapl -Fc -v > /tmp/database.backup'
sudo docker cp postgres:/tmp/database.backup ./$BACKUP_DIR

# BACKUP DA PASTA MEDIA
sudo docker exec -it sapl bash -c 'tar -cvzf media.tar.gz media'
sudo docker cp sapl:/var/interlegis/sapl/media.tar.gz ./$BACKUP_DIR
