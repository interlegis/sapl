
from django.urls.conf import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, \
    SpectacularRedocView
from rest_framework.authtoken.views import obtain_auth_token

from sapl.api.deprecated import SessaoPlenariaViewSet
from sapl.api.views import AppVersionView, recria_token,\
    SaplApiViewSetConstrutor

from .apps import AppConfig


app_name = AppConfig.name

router = SaplApiViewSetConstrutor.router()

# TODO: eliminar endpoint, transferido para SaplApiViewSetConstrutor
# verificar se ainda permanece necessidade desses endpoint's
# /api/sessao-planaria -> /api/sessao/sessaoplenaria/ecidadania
#  /api/sessao-planaria/{pk} -> /api/sessao/sessaoplenaria/{pk}/ecidadania
router.register(r'sessao-plenaria', SessaoPlenariaViewSet,
                basename='sessao_plenaria_old')

urlpatterns_router = router.urls

urlpatterns_api_doc = [
    path('^schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='sapl.api:schema_api'),
         name='swagger_ui_schema_api'),
    path('^schema/redoc/',
         SpectacularRedocView.as_view(url_name='sapl.api:schema_api'),
         name='redoc_schema_api'),
    path('^schema/', SpectacularAPIView.as_view(), name='schema_api'),
]

urlpatterns = [
    path(r'^api/', include(urlpatterns_api_doc)),
    path(r'^api/', include(urlpatterns_router)),

    path(r'^api/version', AppVersionView.as_view()),
    path(r'^api/auth/token$', obtain_auth_token),
    path(r'^api/recriar-token/(?P<pk>\d*)$',
         recria_token, name="recria_token"),
]
