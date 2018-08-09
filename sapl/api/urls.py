from django.conf import settings
from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

import sapl.api.base.urls
import sapl.api.materia.urls
import sapl.api.sessao.urls
from sapl.api.views import ModelChoiceView

from .apps import AppConfig


app_name = AppConfig.name


router = DefaultRouter()
router.registry += sapl.api.materia.urls.router.registry + \
    sapl.api.sessao.urls.router.registry

urlpatterns_router = router.urls

urlpatterns_api = [
    url(r'^model/(?P<content_type>\d+)/(?P<pk>\d*)$',
        ModelChoiceView.as_view(), name='model_list'),
]

if settings.DEBUG:
    urlpatterns_api += [
        url(r'^docs', include('rest_framework_docs.urls')), ]

urlpatterns = [
    url(r'^api/', include(sapl.api.materia.urls)),
    url(r'^api/', include(sapl.api.sessao.urls)),
    url(r'^api/', include(sapl.api.base.urls)),
    url(r'^api/', include(urlpatterns_api)),
    url(r'^api/', include(urlpatterns_router))
]
