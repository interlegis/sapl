from django.conf.urls import url

from compilacao import views

urlpatterns = [
    url(r'^norma/(?P<norma_id>[0-9]+)/compilacao/$',
        views.CompilacaoView.as_view(), name='compilacao'),
    url(r'^norma/(?P<norma_id>[0-9]+)/compilacao/vigencia/' +
        '(?P<iyear>[0-9]+)/(?P<imonth>[0-9]+)/(?P<iday>[0-9]+)/' +
        '(?P<eyear>[0-9]+)/(?P<emonth>[0-9]+)/(?P<eday>[0-9]+)/$',
        views.CompilacaoView.as_view(), name='vigencia'),
    url(r'^norma/(?P<norma_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/$',
        views.DispositivoView.as_view(), name='dispositivo'),
]
