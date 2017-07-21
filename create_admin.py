import os
import sys
import django
from sapl import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")

def create_superuser():
    from django.contrib.auth.models import User

    username = "admin"
    password = os.environ['ADMIN_PASSWORD'] if 'ADMIN_PASSWORD' in os.environ else None
    email = os.environ['ADMIN_EMAIL'] if 'ADMIN_EMAIL' in os.environ else ''

    if User.objects.filter(username=username).exists():
        print("[SUPERUSER] User %s already exists. Exiting without change." % username)
        sys.exit('ADMIN_USER_EXISTS')
    else:
        if not password:
            print("[SUPERUSER] Environment variable $ADMIN_PASSWORD for user %s was not set. Leaving..." % username)
            sys.exit('MISSING_ADMIN_PASSWORD')

        print("[SUPERUSER] Creating superuser...")

        u = User.objects.create_superuser(username=username, password=password, email=email)
        u.save()

        print("[SUPERUSER] Done.")

        sys.exit(0)

if __name__ == '__main__':
    django.setup()
    create_superuser()
