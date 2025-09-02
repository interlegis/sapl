#!/usr/bin/env python
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")


def get_enviroment_admin_password(username):
    password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        print(
            "[SUPERUSER] Environment variable $ADMIN_PASSWORD"
            " for user %s was not set. Leaving..." % username)
        sys.exit('MISSING_ADMIN_PASSWORD')
    return password


def create_user_interlegis():
    from django.contrib.auth.models import User

    password = get_enviroment_admin_password('interlegis')
    print("[SUPERUSER INTERLEGIS] Creating interlegis superuser...")
    user, created = User.objects.get_or_create(username='interlegis')
    if not created:
        print("[SUPERUSER INTERLEGIS] User interlegis already exists."
              " Updating password.")
    user.is_superuser = True
    user.is_staff = True
    user.set_password(password)
    user.save()
    print("[SUPERUSER INTERLEGIS] Done.")


def create_superuser():
    from django.contrib.auth.models import User

    username = "admin"
    email = os.environ.get('ADMIN_EMAIL', '')

    if User.objects.filter(username=username).exists():
        print("[SUPERUSER] User %s already exists."
              " Exiting without change." % username)
        sys.exit('ADMIN_USER_EXISTS')
    else:
        password = get_enviroment_admin_password(username)

        print("[SUPERUSER] Creating superuser...")

        u = User.objects.create_superuser(
            username=username, password=password, email=email)
        u.save()

        print("[SUPERUSER] Done.")

        sys.exit(0)


if __name__ == '__main__':
    django.setup()
    create_user_interlegis()  # must come before create_superuser
    create_superuser()
