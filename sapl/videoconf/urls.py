
from .apps import AppConfig
from .views import ChatView, VideoConferenciaCrud
from django.conf.urls import include, url

app_name = AppConfig.name

urlpatterns = [
    url(r'^videoconferencia/chat/(?P<pk>[0-9]+)$',
        ChatView.as_view(), name='chat-session'),
    url(r'^videoconferencia/',
        include(VideoConferenciaCrud.get_urls()), name='videoconferencia'),
]
