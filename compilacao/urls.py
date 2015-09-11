from django.conf.urls import url

from compilacao import views

urlpatterns = [
    url(r'^norma/(?P<norma_id>\d+)/compilacao/',
        views.CompilacaoView.as_view(), name='compilacao'),
]
