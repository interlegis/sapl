#!/bin/bash

# As seen in http://tutos.readthedocs.org/en/latest/source/ndg.html

SAPL_DIR=/var/interlegis/sapl

# Seta um novo diretório foi passado como raiz para o SAPL
# caso esse tenha sido passado como parâmetro
if [ "$1" ]
then
    SAPL_DIR="$1"
fi

NAME="SAPL"                                     # Name of the application (*)
DJANGODIR=$SAPL_DIR                    # Django project directory (*)
SOCKFILE=$SAPL_DIR/gunicorn.sock    # we will communicate using this unix socket (*)
USER=`whoami`                                   # the user to run as (*)
GROUP=`whoami`                                  # the group to run as (*)
NUM_WORKERS=3                                   # how many worker processes should Gunicorn spawn (*)
                                                # NUM_WORKERS = 2 * CPUS + 1
DJANGO_SETTINGS_MODULE=sapl.settings            # which settings file should Django use (*)
DJANGO_WSGI_MODULE=sapl.wsgi                    # WSGI module name (*)

echo "Starting $NAME as `whoami`"

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user $USER \
  --bind=unix:$SOCKFILE
