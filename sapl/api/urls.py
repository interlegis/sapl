
from django.conf.urls import include, url
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, \
    SpectacularRedocView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from sapl.api.deprecated import MateriaLegislativaViewSet, SessaoPlenariaViewSet, \
    AutoresProvaveisListView, AutoresPossiveisListView, AutorListView, \
    ModelChoiceView
from sapl.api.views import AppVersionView, recria_token
from sapl.api.viewset import SaplApiViewSetConstrutor

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

urlpatterns_api_doc = [
    # Optional UI:
    url('^schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='sapl.api:schema_api'), name='swagger_ui_schema_api'),
    url('^schema/redoc/',
        SpectacularRedocView.as_view(url_name='sapl.api:schema_api'), name='redoc_schema_api'),
    # YOUR PATTERNS
    url('^schema/', SpectacularAPIView.as_view(), name='schema_api'),
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
    url(r'^api/version', AppVersionView.as_view()),
    url(r'^api/recriar-token/(?P<pk>\d*)$', recria_token, name="recria_token"),

    url(r'^api/auth/token$', obtain_auth_token),

    # implementar caminho para autenticação
    # https://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/
    # url(r'^api/auth/', include('rest_framework.urls', namespace='rest_framework')),
]
