from django.urls import include, path, re_path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from rest_framework.authtoken.views import obtain_auth_token

from sapl.api.deprecated import SessaoPlenariaViewSet
from sapl.api.views import (AppVersionView, SaplApiViewSetConstrutor,
                            recria_token)

from .apps import AppConfig

app_name = AppConfig.name

router = SaplApiViewSetConstrutor.router()

# TODO: eliminar endpoint, transferido para SaplApiViewSetConstrutor
# verificar se ainda permanece necessidade desses endpoint's
# /api/sessao-planaria -> /api/sessao/sessaoplenaria/ecidadania
#  /api/sessao-planaria/{pk} -> /api/sessao/sessaoplenaria/{pk}/ecidadania
router.register(
    r"sessao-plenaria", SessaoPlenariaViewSet, basename="sessao_plenaria_old"
)

urlpatterns_router = router.urls

urlpatterns_api_doc = [
    re_path(
        "^schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="sapl.api:schema_api"),
        name="swagger_ui_schema_api",
    ),
    re_path(
        "^schema/redoc/",
        SpectacularRedocView.as_view(url_name="sapl.api:schema_api"),
        name="redoc_schema_api",
    ),
    re_path("^schema/", SpectacularAPIView.as_view(), name="schema_api"),
]

urlpatterns = [
    path("api/", include(urlpatterns_api_doc)),
    path("api/", include(urlpatterns_router)),
    re_path(r"^api/version", AppVersionView.as_view()),
    path("api/auth/token", obtain_auth_token),
    re_path(r"^api/recriar-token/(?P<pk>\d*)$", recria_token, name="recria_token"),
]
