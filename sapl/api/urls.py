from django.conf import settings
from django.conf.urls import include, url
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from sapl.api.deprecated import MateriaLegislativaViewSet, SessaoPlenariaViewSet,\
    AutoresProvaveisListView, AutoresPossiveisListView, AutorListView,\
    ModelChoiceView
from sapl.api.views import SaplApiViewSetConstrutor

from .apps import AppConfig


app_name = AppConfig.name


router = DefaultRouter()
router.register(r'materia$', MateriaLegislativaViewSet)
router.register(r'sessao-plenaria', SessaoPlenariaViewSet)


for app, built_sets in SaplApiViewSetConstrutor._built_sets.items():
    for view_prefix, viewset in built_sets.items():
        router.register(app.label + '/' +
                        view_prefix._meta.model_name, viewset)


urlpatterns_router = router.urls

urlpatterns_api_doc = []
if 'drf_yasg' in settings.INSTALLED_APPS:
    from drf_yasg import openapi
    from drf_yasg.views import get_schema_view
    schema_view = get_schema_view(
        openapi.Info(
            title="Sapl API - docs",
            default_version='v1',
            description="Sapl API  - Docs - Configuração Básica",
        ),
        url=settings.SITE_URL,
        public=True,
        permission_classes=(permissions.AllowAny,),
    )

    urlpatterns_api_doc = [
        url(r'^docs/swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
        url(r'^docs/swagger/$',
            schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        url(r'^docs/redoc/$',
            schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]

# TODO: refatorar para customização da api automática
deprecated_urlpatterns_api = [
    url(r'^autor/provaveis',
        AutoresProvaveisListView.as_view(), name='autores_provaveis_list'),
    url(r'^autor/possiveis',
        AutoresPossiveisListView.as_view(), name='autores_possiveis_list'),

    url(r'^autor', AutorListView.as_view(), name='autor_list'),

    url(r'^model/(?P<content_type>\d+)/(?P<pk>\d*)$',
        ModelChoiceView.as_view(), name='model_list'),


]

urlpatterns = [
    url(r'^api/', include(deprecated_urlpatterns_api)),
    url(r'^api/', include(urlpatterns_api_doc)),
    url(r'^api/', include(urlpatterns_router)),


    # implementar caminho para autenticação
    # https://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/
    # url(r'^api/auth/', include('rest_framework.urls', namespace='rest_framework')),
]
