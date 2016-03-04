"""
WSGI config for sapl project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/

  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")

application = get_wsgi_application()
