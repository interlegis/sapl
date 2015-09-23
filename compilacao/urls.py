from django.conf.urls import url

from compilacao import views

urlpatterns = [
    url(r'^norma/(?P<norma_id>[0-9]+)/compilacao/$',
        views.CompilacaoView.as_view(), name='compilacao'),



    url(r'^norma/(?P<norma_id>[0-9]+)/compilacao/vigencia/(?P<sign>.+)/$',
        views.CompilacaoView.as_view(), name='vigencia'),

    url(r'^norma/(?P<norma_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/$',
        views.DispositivoView.as_view(), name='dispositivo'),
]
