from datetime import date, datetime

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.base import TemplateView
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

# anular_protocolo_crud = build_crud(
#     Protocolo, '', [

#         [_('Indentificação do Protocolo'),
#          [('numero', 6), ('ano', 6)],
#             [('justificativa_anulacao', 12)]],
#     ])


def get_tipos_materia():
    return [('', 'Selecione')] \
            + [(t.id, t.sigla + ' - ' + t.descricao)
               for t in TipoMateriaLegislativa.objects.all()]


def get_range_anos():
    return [('', 'Selecione')] \
            + [(year, year) for year in range(date.today().year, 1960, -1)]


def get_tipos_documento():
    return [('', 'Selecione')] \
            + [(t.id, t.sigla + ' - ' + t.descricao)
               for t in TipoDocumentoAdministrativo.objects.all()]


class ProtocoloListView(ListView):
    template_name = 'protocoloadm/protocolo_list.html'
    context_object_name = 'protocolos'
    model = Protocolo
    paginate_by = 10


class ProtocoloForm(forms.Form):

    TIPOS_PROTOCOLO = [('', 'Selecione'),
                       ('0', 'Enviado'),
                       ('1', 'Recebido')]

    YEARS = get_range_anos()

    tipo_protocolo = forms.ChoiceField(required=False,
                                       label='Tipo de Protocolo',
                                       choices=TIPOS_PROTOCOLO,
                                       widget=forms.Select(
                                           attrs={'class': 'selector'}))

    numero_protocolo = forms.CharField(
        label='Número de Protocolo', required=False)
    ano = forms.ChoiceField(required=False,
                            label='Ano',
                            choices=YEARS,
                            widget=forms.Select(
                                attrs={'class': 'selector'}))

    inicial = forms.DateField(label='Data Inicial',
                              required=False,
                              widget=forms.TextInput(
                                attrs={'class': 'dateinput'}))

    final = forms.DateField(label='Data Final', required=False,
                            widget=forms.TextInput(
                                attrs={'class': 'dateinput'}))

    natureza_processo = forms.CharField(
        label='Natureza Processo', required=False)
    tipo_documento = forms.ChoiceField(required=False,
                                       label='Tipo de Documento',
                                       choices=get_tipos_documento(),
                                       widget=forms.Select(
                                           attrs={'class': 'selector'}))

    interessado = forms.CharField(label='Interessado', required=False)
    tipo_materia = forms.ChoiceField(required=False,
                                     label='Tipo Matéria',
                                     choices=get_tipos_materia(),
                                     widget=forms.Select(
                                         attrs={'class': 'selector'}))

    autor = forms.CharField(label='Autor', required=False)
    assunto = forms.CharField(label='Assunto', required=False)


class ProtocoloPesquisaView(TemplateView, FormMixin):
    template_name = 'protocoloadm/protocolo_pesquisa.html'
    form_class = ProtocoloForm()
    context_object_name = 'protocolos'
    paginate_by = 10

    extra_context = {}

    def get_success_url(self):
        return reverse('protocolo')

    def get(self, request, *args, **kwargs):
        form = ProtocoloForm()
        return self.render_to_response({'form': form})

    def get_form(self, data=None, files=None, **kwargs):
        return ProtocoloForm()

    def get_context_data(self, **kwargs):
        context = super(ProtocoloPesquisaView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def post(self, request, *args, **kwargs):
        form = ProtocoloForm(request.POST or None)

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
                    request.POST['inicial'],
                    '%d/%m/%Y').strftime('%Y-%m-%d')

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
            self.extra_context['form'] = form

            # return self.form_valid(form)
            return self.render_to_response(
                {'protocolos': protocolos}
            )
        else:
            return self.form_invalid(form)


class AnularProcoloAdmForm(forms.Form):

    YEARS = get_range_anos()

    numero_protocolo = forms.CharField(
        label='Número de Protocolo', required=True)
    ano_protocolo = forms.ChoiceField(required=False,
                                      label='Ano',
                                      choices=YEARS,
                                      widget=forms.Select(
                                          attrs={'class': 'selector'}))
    justificativa_anulacao = forms.CharField(
        widget=forms.Textarea, label='Motivo', required=True)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AnularProtocoloAdmView(FormMixin, TemplateView):
    template_name = 'protocoloadm/anular_protocoloadm.html'

    def get_success_url(self):
        return reverse('anular_protocolo')

    def get(self, request, *args, **kwargs):
        form = AnularProcoloAdmForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):

        form = AnularProcoloAdmForm(request.POST)

        if form.is_valid():

            numero = request.POST['numero_protocolo']
            ano = request.POST['ano_protocolo']
            justificativa_anulacao = strip_tags(
                request.POST['justificativa_anulacao'])
            user_anulacao = "NOUSER"  # TODO get user from session
            ip_addr = get_client_ip(request)

            try:
                protocolo = Protocolo.objects.get(numero=numero, ano=ano)

                if protocolo.anulado:
                    errors = form._errors.setdefault(
                        forms.forms.NON_FIELD_ERRORS,
                        forms.util.ErrorList())
                    errors.append("Procolo %s/%s já encontra-se anulado"
                                  % (numero, ano))
                    return self.form_invalid(form)

                protocolo.anulado = True
                protocolo.justificativa_anulacao = justificativa_anulacao
                protocolo.user_anulacao = user_anulacao
                protocolo.ip_anulacao = ip_addr
                protocolo.save()
                message = "Protocolo criado com sucesso"
                return render(request,
                              reverse("anular_protocolo"),
                              {'form': form, 'message': message})

            except ObjectDoesNotExist:
                errors = form._errors.setdefault(
                    forms.forms.NON_FIELD_ERRORS, forms.util.ErrorList())
                errors.append("Procolo %s/%s não existe" % (numero, ano))
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)
