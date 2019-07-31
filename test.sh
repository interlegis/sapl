#!/bin/bash

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


python3 manage.py migrate
#./scripts/django/check_migrations.sh
py.test --create-db
