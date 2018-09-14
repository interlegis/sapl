from django.conf.urls import url
from sapl.api.base.views import AutorListView, AutoresPossiveisListView,\
    AutoresProvaveisListView

# Não adicione app_name
# app_name = AppConfig.name


urlpatterns = [
    url(r'^autor/$', AutorListView.as_view(), name='autor_list'),
    url(r'^autor/provaveis',
        AutoresProvaveisListView.as_view(), name='autores_provaveis_list'),
    url(r'^autor/possiveis',
        AutoresPossiveisListView.as_view(), name='autores_possiveis_list'),
]
