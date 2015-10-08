from datetime import datetime

from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from materia.models import TipoMateriaLegislativa
from sapl.crud import build_crud

from .models import (DocumentoAcessorioAdministrativo, DocumentoAdministrativo,
                     Protocolo, StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)

tipo_documento_administrativo_crud = build_crud(
    TipoDocumentoAdministrativo, '', [

        [_('Tipo Documento Administrativo'),
         [('sigla', 4), ('descricao', 8)]],
    ])

documento_administrativo_crud = build_crud(
    DocumentoAdministrativo, '', [

        [_('Indentificação Básica'),
         [('tipo', 4), ('numero', 4), ('ano', 4)],
            [('data', 6), ('numero_protocolo', 6)],
            [('assunto', 12)],
            [('interessado', 6), ('tramitacao', 6)],
            [('texto_integral', 12)]],

        [_('Outras Informações'),
         [('dias_prazo', 6), ('data_fim_prazo', 6)],
            [('observacao', 12)]],
    ])

documento_acessorio_administrativo_crud = build_crud(
    DocumentoAcessorioAdministrativo, '', [

        [_('Documento Acessório'),
         [('tipo', 4), ('nome', 4), ('data', 4)],
            [('autor', 12)],
            [('arquivo', 12)],
            [('assunto', 12)]],
    ])

status_tramitacao_administrativo_crud = build_crud(
    StatusTramitacaoAdministrativo, '', [

        [_('Status Tramitação Administrativo'),
         [('indicador', 3),
            ('sigla', 2),
            ('descricao', 7)]],
    ])

tramitacao_administrativo_crud = build_crud(
    TramitacaoAdministrativo, '', [

        [_('Tramitação'),
         [('data_tramitacao', 4), ('unidade_tramitacao_local', 8)],
            [('status', 4), ('unidade_tramitacao_destino', 8)],
            [('data_encaminhamento', 6), ('data_fim_prazo', 6)],
            [('texto', 12)]],
    ])

protocolo_documento_crud = build_crud(
    Protocolo, '', [

        [_('Indentificação Documento'),
         [('tipo_protocolo', 12)],
            [('tipo_documento', 6), ('numero_paginas', 6)],
            [('assunto_ementa', 12)],
            [('interessado', 12)],
            [('observacao', 12)]],
    ])

protocolo_materia_crud = build_crud(
    Protocolo, '', [

        [_('Indentificação da Matéria'),
         [('tipo_materia', 6), ('numero_paginas', 6)],
            [('assunto_ementa', 12)],
            [('autor', 12)],
            [('observacao', 12)]],
    ])

anular_protocolo_crud = build_crud(
    Protocolo, '', [

        [_('Indentificação do Protocolo'),
         [('numero', 6), ('ano', 6)],
            [('justificativa_anulacao', 12)]],
    ])


class ProtocoloForm(forms.Form):
    tipo_protocolo = forms.CharField(required=False)
    numero_protocolo = forms.CharField(required=False)
    ano = forms.CharField(required=False)
    inicial = forms.DateField(required=False)
    final = forms.DateField(required=False)
    natureza_processo = forms.CharField(required=False)
    tipo_documento = forms.CharField(required=False)
    interessado = forms.CharField(required=False)
    tipo_materia = forms.CharField(required=False)
    autor = forms.CharField(required=False)
    assunto = forms.CharField(required=False)


class ProtocoloPesquisaView(ListView, FormMixin):
    template_name = 'protocoloadm/protocolo_pesquisa.html'
    form_class = ProtocoloForm

    extra_context = {}

    def get_success_url(self):
        return reverse('protocolo')

    def get_context_data(self, **kwargs):
        context = super(ProtocoloPesquisaView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def get_queryset(self):
        return Protocolo.objects.all()

    def get_tipo_documento(self):
        return TipoDocumentoAdministrativo.objects.all()

    def get_tipo_materia(self):
        return TipoMateriaLegislativa.objects.all()

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            kwargs = {}

            # format = '%Y-%m-%d'

            if request.POST['tipo_protocolo']:
                kwargs['tipo_protocolo'] = request.POST['tipo_protocolo']

            if request.POST['numero_protocolo']:
                kwargs['numero'] = request.POST['numero_protocolo']

            if request.POST['ano']:
                kwargs['ano'] = request.POST['ano']

            if request.POST['inicial']:
                kwargs['data'] = datetime.strptime(
                    request.POST['inicial'], '%d/%m/%Y').strftime('%Y-%m-%d')

            # if request.POST['final']:
            #     kwargs['final'] = request.POST['final']

            if request.POST['tipo_documento']:
                kwargs['tipo_documento'] = request.POST['tipo_documento']

            if request.POST['interessado']:
                kwargs['interessado'] = request.POST['interessado']

            if request.POST['tipo_materia']:
                kwargs['tipo_materia'] = request.POST['tipo_materia']

            if request.POST['autor']:
                kwargs['autor'] = request.POST['autor']

            if request.POST['assunto']:
                kwargs['assunto'] = request.POST['assunto']

            protocolos = Protocolo.objects.filter(
                **kwargs)

            self.extra_context['protocolos'] = protocolos

            return self.form_valid(form)
        else:
            return self.form_invalid(form)
