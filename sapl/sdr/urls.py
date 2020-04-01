
from .apps import AppConfig
from .views import ChatView, DeliberacaoRemotaCrud
from django.conf.urls import include, url

app_name = AppConfig.name

urlpatterns = [
    url(r'^sdr/chat/(?P<pk>[0-9]+)$',
        ChatView.as_view(), name='chat-session'),
    url(r'^sdr/',
        include(DeliberacaoRemotaCrud.get_urls()), name='deliberacaoremota'),
]
