"""sapl URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

from comissoes.views import tipo_comissao_crud, comissao_crud
from parlamentares.views import (legislatura_crud, coligacao_crud,
                                 partido_crud, tipo_dependente_crud,
                                 nivel_instrucao_crud, tipo_afastamento_crud,
                                 tipo_militar_crud)


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^admin/', include(admin.site.urls)),

    # main apps
    url(r'^comissoes/', include(comissao_crud.urls)),
    url(r'^sessao/', include('sessao.urls')),

    # system data
    # comissao
    url(r'^sistema/comissoes/tipo/', include(tipo_comissao_crud.urls)),
    url(r'^sistema/comissoes/tipo/', include(tipo_comissao_crud.urls)),

    # parlamentares
    url(r'^sistema/parlamentares/legislatura/',
        include(legislatura_crud.urls)),
    url(r'^sistema/parlamentares/tipo-dependente/',
        include(tipo_dependente_crud.urls)),
    url(r'^sistema/parlamentares/nivel-instrucao/',
        include(nivel_instrucao_crud.urls)),
    url(r'^sistema/parlamentares/coligacao/', include(coligacao_crud.urls)),
    url(r'^sistema/parlamentares/tipo-afastamento/',
        include(tipo_afastamento_crud.urls)),
    url(r'^sistema/parlamentares/tipo-militar/',
        include(tipo_militar_crud.urls)),
    url(r'^sistema/parlamentares/partido/', include(partido_crud.urls)),
]
