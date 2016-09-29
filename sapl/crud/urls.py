from builtins import LookupError

from django import apps
from django.conf.urls import include, url
from django.contrib.auth.management import _get_all_permissions
from django.core import exceptions
from django.db import models, router
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.translation import string_concat


urlpatterns = [
    url(r'', include('stub_app.urls')),
]
