#!/bin/sh

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
    echo "SOLR_URL = ""${SOLR_URL-'http://saplsolr:8983/solr/sapl'}" >> $FILENAME

    
    echo "[ENV FILE] done."
}

create_env

#python3 manage.py bower install

/bin/sh busy-wait.sh $DATABASE_URL

# manage.py migrate --noinput nao funcionava
yes yes | python3 manage.py migrate
#python3 manage.py collectstatic --no-input
# python3 manage.py rebuild_index --noinput &


## SOLR

CORE_EXISTS=$(curl -s 'http://saplsolr:8983/solr/admin/cores?action=STATUS&core=sapl' | jq '.status.sapl != null')

if [ CORE_EXISTS = false ]; then

    echo "CREATING CORE sapl..."

    mkdir solr_data/sapl && cp -r solr/sapl_configset/* solr_data/sapl/

    CREATE_CORE=$(curl -s "http://saplsolr:8983/solr/admin/cores?action=CREATE&name=sapl")
    RESULT_CODE=$(echo $CREATE_CORE | jq '.error.code')
    RESULT_MSG=$(echo $CREATE_CORE | jq '.error.msg')

    if [ $RESULT_CODE -eq 500 ]; then
        echo "Erro ao criar core sapl ["$RESULT_CODE"], mensagem:"$RESULT_MSG
    else
        echo "Solr core criado com sucesso."
    fi
else
    echo "Core solr existente."
fi

NUM_DOCS=$(curl -s 'http://saplsolr:8983/solr/admin/cores?action=STATUS&core=sapl' | jq -r '.status.sapl.index.numDocs')
echo "Documentos indexados:"$NUM_DOCS

if [ $NUM_DOCS -eq 0 ]; then
   echo "Reconstruindo índice textual totalmente..."
   yes | python3 manage.py rebuild_index &
   echo "Reconstrução completa."
else
   echo "Atualizando o índice textual..."
   yes | python3 manage.py update_index &
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


/bin/sh gunicorn_start.sh no-venv &
/usr/sbin/nginx -g "daemon off;"
