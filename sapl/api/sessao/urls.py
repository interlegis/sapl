from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
from sapl.api.sessao.views import SessaoPlenariaViewSet,\
    SessaoPlenariaOldViewSet

# Não adicione app_name
# app_name = AppConfig.name

router = DefaultRouter()
router.register(r'sessao-plenaria-old', SessaoPlenariaOldViewSet,
                base_name='sessao-plenaria-old')
router.register(r'sessao-plenaria', SessaoPlenariaViewSet)

urlpatterns = [
]
