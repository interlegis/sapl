from django.conf import settings
from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from sapl.api.views import (AutorListView, MateriaLegislativaViewSet,
                            ModelChoiceView, SessaoPlenariaViewSet)

from .apps import AppConfig

app_name = AppConfig.name


router = DefaultRouter()
router.register(r'materia', MateriaLegislativaViewSet)
router.register(r'sessao-plenaria', SessaoPlenariaViewSet)
urlpatterns_router = router.urls

urlpatterns_api = [

    url(r'^autor', AutorListView.as_view(), name='autor_list'),

    url(r'^model/(?P<content_type>\d+)/(?P<pk>\d*)$',
        ModelChoiceView.as_view(), name='model_list'),

]

if settings.DEBUG:
    urlpatterns_api += [
        url(r'^docs', include('rest_framework_docs.urls')), ]

urlpatterns = [
    url(r'^api/', include(urlpatterns_api)),
    url(r'^api/', include(urlpatterns_router))
]
