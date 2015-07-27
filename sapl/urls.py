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

from comissoes.urls import comissoes_urls
from comissoes.views import (cargo_crud, periodo_composicao_crud,
                             tipo_comissao_crud)
from lexml.views import lexml_provedor_crud, lexml_publicador_crud
from materia.views import (autor_crud, orgao_crud, origem_crud,
                           regime_tramitacao_crud, status_tramitacao_crud,
                           tipo_autor_crud, tipo_documento_crud,
                           tipo_fim_relatoria_crud, tipo_materia_crud,
                           tipo_proposicao_crud, unidade_tramitacao_crud)
from norma.views import assunto_norma_crud, tipo_norma_crud
from parlamentares.views import (cargo_mesa_crud, coligacao_crud,
                                 legislatura_crud, nivel_instrucao_crud,
                                 partido_crud, sessao_legislativa_crud,
                                 tipo_afastamento_crud, tipo_dependente_crud,
                                 tipo_militar_crud)
from sessao.urls import sessao_urls
from sessao.views import (tipo_expediente_crud, tipo_resultado_votacao_crud,
                          tipo_sessao_crud)

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^admin/', include(admin.site.urls)),

    # main apps
    url(r'^comissoes/', include(comissoes_urls)),
    url(r'^sessao/', include(sessao_urls)),

    # SYSTEM DATA

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

    # mesa diretora
    url(r'^sistema/mesa-diretora/sessao-legislativa/',
        include(sessao_legislativa_crud.urls)),
    url(r'^sistema/mesa-diretora/cargo-mesa/',
        include(cargo_mesa_crud.urls)),

    # comissao
    url(r'^sistema/comissoes/cargo/', include(cargo_crud.urls)),
    url(r'^sistema/comissoes/periodo-composicao/',
        include(periodo_composicao_crud.urls)),
    url(r'^sistema/comissoes/tipo/', include(tipo_comissao_crud.urls)),

    # bancada
    # TODO

    # proposições
    url(r'^sistema/proposicoes/tipo/', include(tipo_proposicao_crud.urls)),
    url(r'^sistema/proposicoes/autor/', include(autor_crud.urls)),

    # materia
    url(r'^sistema/materia/tipo/', include(tipo_materia_crud.urls)),
    url(r'^sistema/materia/regime-tramitacao/',
        include(regime_tramitacao_crud.urls)),
    url(r'^sistema/materia/tipo-autor/', include(tipo_autor_crud.urls)),
    url(r'^sistema/materia/tipo-documento/',
        include(tipo_documento_crud.urls)),
    url(r'^sistema/materia/tipo-fim-relatoria/',
        include(tipo_fim_relatoria_crud.urls)),
    url(r'^sistema/materia/unidade-tramitacao/',
        include(unidade_tramitacao_crud.urls)),
    url(r'^sistema/materia/origem/', include(origem_crud.urls)),
    url(r'^sistema/materia/autor/', include(autor_crud.urls)),
    url(r'^sistema/materia/status-tramitacao/',
        include(status_tramitacao_crud.urls)),
    url(r'^sistema/materia/orgao/', include(orgao_crud.urls)),

    # norma
    url(r'^sistema/norma/tipo/', include(tipo_norma_crud.urls)),
    url(r'^sistema/norma/assunto/', include(assunto_norma_crud.urls)),

    # sessao plenaria
    url(r'^sistema/sessao-plenaria/tipo/', include(tipo_sessao_crud.urls)),
    url(r'^sistema/sessao-plenaria/tipo-resultado-votacao/',
        include(tipo_resultado_votacao_crud.urls)),
    url(r'^sistema/sessao-plenaria/tipo-expediente/',
        include(tipo_expediente_crud.urls)),

    # lexml
    url(r'^sistema/lexml/provedor/', include(lexml_provedor_crud.urls)),
    url(r'^sistema/lexml/publicador/', include(lexml_publicador_crud.urls)),

    url(r'^sistema/', TemplateView.as_view(template_name='sistema.html')),
]
