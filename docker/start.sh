#!/usr/bin/env bash

create_env() {
    echo "[ENV FILE] creating .env file..."
    # check if file exists
    if [ -f "/var/interlegis/sapl/data/secret.key" ]; then
        KEY=`cat /var/interlegis/sapl/data/secret.key`
    else
        KEY=`python3 genkey.py`
        echo $KEY > data/secret.key
    fi

    FILENAME="/var/interlegis/sapl/sapl/.env"

    if [ -z "${DATABASE_URL:-}" ]; then
        DATABASE_URL="postgresql://sapl:sapl@sapldb:5432/sapl"
    fi

    # ALWAYS replace the content of .env variable
    # If want to conditionally create only if absent then use IF below
    #    if [ ! -f $FILENAME ]; then

    touch $FILENAME


    # explicitly use '>' to erase any previous content
    echo "SECRET_KEY="$KEY > $FILENAME
    # now only appends
    echo "DATABASE_URL = "$DATABASE_URL >> $FILENAME
    echo "DEBUG = ""${DEBUG-False}" >> $FILENAME
    echo "EMAIL_USE_TLS = ""${USE_TLS-True}" >> $FILENAME
    echo "EMAIL_PORT = ""${EMAIL_PORT-587}" >> $FILENAME
    echo "EMAIL_HOST = ""${EMAIL_HOST-''}" >> $FILENAME
    echo "EMAIL_HOST_USER = ""${EMAIL_HOST_USER-''}" >> $FILENAME
    echo "EMAIL_HOST_PASSWORD = ""${EMAIL_HOST_PASSWORD-''}" >> $FILENAME
    echo "EMAIL_SEND_USER = ""${EMAIL_HOST_USER-''}" >> $FILENAME
    echo "DEFAULT_FROM_EMAIL = ""${EMAIL_HOST_USER-''}" >> $FILENAME
    echo "SERVER_EMAIL = ""${EMAIL_HOST_USER-''}" >> $FILENAME
    echo "USE_SOLR = ""${USE_SOLR-False}" >> $FILENAME
    echo "SOLR_COLLECTION = ""${SOLR_COLLECTION-sapl}" >> $FILENAME
    echo "SOLR_URL = ""${SOLR_URL-http://localhost:8983}" >> $FILENAME

    
    echo "[ENV FILE] done."
}

create_env

/bin/bash busy-wait.sh $DATABASE_URL

yes yes | python3 manage.py migrate


## SOLR
USE_SOLR="${USE_SOLR:=False}"
SOLR_URL="${SOLR_URL:=http://localhost:8983}"
SOLR_COLLECTION="${SOLR_COLLECTION:=sapl}"

NUM_SHARDS=${NUM_SHARDS:=1}
RF=${RF:=1}
MAX_SHARDS_PER_NODE=${MAX_SHARDS_PER_NODE:=1}

if [ "${USE_SOLR-False}" == "True" ] || [ "${USE_SOLR-False}" == "true" ]; then

    echo "SOLR configurations"
    echo "==================="
    echo "URL: $SOLR_URL"
    echo "COLLECTION: $SOLR_COLLECTION"
    echo "NUM_SHARDS: $NUM_SHARDS"
    echo "REPLICATION FACTOR: $RF"
    echo "MAX SHARDS PER NODE: $MAX_SHARDS_PER_NODE"
    echo "========================================="

    echo "running solr script"
    /bin/bash check_solr.sh $SOLR_URL
    CHECK_SOLR_RETURN=$?

    if [ $CHECK_SOLR_RETURN == 1 ]; then
        echo "Connecting to solr..."
        python3 solr_api.py -u $SOLR_URL -c $SOLR_COLLECTION -s $NUM_SHARDS -rf $RF -ms $MAX_SHARDS_PER_NODE &
        # python3 manage.py rebuild_index --noinput &
    else
        echo "Solr is offline, not possible to connect."
    fi

else
    echo "Suporte a SOLR não inicializado."
fi

echo "Criando usuário admin..."

user_created=$(python3 create_admin.py 2>&1)

echo $user_created

cmd=$(echo $user_created | grep 'ADMIN_USER_EXISTS')
user_exists=$?

cmd=$(echo $user_created | grep 'MISSING_ADMIN_PASSWORD')
lack_pwd=$?

if [ $user_exists -eq 0 ]; then
   echo "[SUPERUSER CREATION] User admin already exists. Not creating"
fi

if [ $lack_pwd -eq 0 ]; then
   echo "[SUPERUSER] Environment variable $ADMIN_PASSWORD for superuser admin was not set. Leaving container"
   # return -1
fi

echo "-------------------------------------"
echo "| ███████╗ █████╗ ██████╗ ██╗       |"
echo "| ██╔════╝██╔══██╗██╔══██╗██║       |"
echo "| ███████╗███████║██████╔╝██║       |"
echo "| ╚════██║██╔══██║██╔═══╝ ██║       |"
echo "| ███████║██║  ██║██║     ███████╗  |"
echo "| ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝  |"
echo "-------------------------------------"

/bin/sh gunicorn_start.sh &
/usr/sbin/nginx -g "daemon off;"
