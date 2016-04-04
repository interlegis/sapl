DJANGODIR=/home/sapl31/sapl                     # Django project directory (*)
DJANGO_SETTINGS_MODULE=sapl.settings            # which settings file should Django use (*)
DJANGO_WSGI_MODULE=sapl.wsgi                    # WSGI module name (*)

cd $DJANGODIR
source ~/.virtualenvs/sapl/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

gunicorn --bind 10.1.2.119:8000 sapl.wsgi:application
