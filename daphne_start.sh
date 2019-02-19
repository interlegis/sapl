#!/bin/bash

# As seen in http://tutos.readthedocs.org/en/latest/source/ndg.html

SAPL_DIR="/var/interlegis/sapl"

# Seta um novo diretório foi passado como raiz para o SAPL
# caso esse tenha sido passado como parâmetro
if [ "$1" ]
then
    SAPL_DIR="$1"
fi

NAME="SAPL"                                     # Name of the application (*)
DJANGODIR=/var/interlegis/sapl/                    # Django project directory (*)
SOCKFILE=/var/interlegis/sapl/run/daphne.sock    # we will communicate using this unix socket (*)
USER=`whoami`                                   # the user to run as (*)
GROUP=`whoami`                                  # the group to run as (*)
NUM_WORKERS=3                                   # how many worker processes should Gunicorn spawn (*)
                                                # NUM_WORKERS = 2 * CPUS + 1
TIMEOUT=60
MAX_REQUESTS=100                                # number of requests before restarting worker
DJANGO_SETTINGS_MODULE=sapl.settings            # which settings file should Django use (*)
DJANGO_ASGI_MODULE=sapl.asgi                    # WSGI module name (*)

echo "Starting $NAME as `whoami` on base dir $SAPL_DIR"

# parameter can be passed to run without virtualenv
if [[ "$@" != "no-venv" ]]; then
    # Activate the virtual environment
    cd $DJANGODIR
    source /var/interlegis/.virtualenvs/sapl/bin/activate
    export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
    export PYTHONPATH=$DJANGODIR:$PYTHONPATH
fi

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
exec daphne \
    -u $SOCKFILE ${DJANGO_ASGI_MODULE}:application \
    --access-log /var/log/sapl/daphne_access.log \
    -v2

