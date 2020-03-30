
from .apps import AppConfig
from .views import VideoConferenciaView
from django.conf.urls import url

app_name = AppConfig.name

urlpatterns = [
    url(r'^videoconf/$', VideoConferenciaView.as_view(), name='videoconferencia'),
]
