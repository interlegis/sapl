DJANGODIR=/var/interlegis/sapl                     # Django project directory (*)
DJANGO_SETTINGS_MODULE=sapl.settings            # which settings file should Django use (*)
DJANGO_WSGI_MODULE=sapl.wsgi                    # WSGI module name (*)

cd $DJANGODIR
source /var/interlegis/.virtualenvs/sapl/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Get eth0 IP and filter out the netmask portion (/24, e.g.)
IP=`ip addr | grep 'inet .* eth0' | awk '{print $2}' | sed 's/\/[0-9]*//'`

gunicorn --bind $IP:8000 sapl.wsgi:application
