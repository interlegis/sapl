from datetime import date, datetime
from re import sub

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Fieldset, Layout, Submit
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from vanilla import GenericView

from materia.models import Proposicao, TipoMateriaLegislativa
from sapl.crud import build_crud

from .models import (Autor, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, Protocolo,
                     StatusTramitacaoAdministrativo,
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

TIPOS_PROTOCOLO = [('', 'Selecione'),
                   ('0', 'Enviado'),
                   ('1', 'Recebido')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class ProtocoloForm(forms.Form):

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

    # TODO: como pesquisar???
    natureza_processo = forms.ChoiceField(required=False,
                                          label='Natureza Processo',
                                          choices=[
                                              ('0', 'Administrativo'),
                                              ('1', 'Legislativo'),
                                              ('', 'Ambos')],
                                          widget=forms.RadioSelect(
                                              renderer=HorizontalRadioRenderer)
                                          )

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


class ProtocoloListView(FormMixin, ListView):
    template_name = 'protocoloadm/protocolo_list.html'
    context_object_name = 'protocolos'
    model = Protocolo
    paginate_by = 10

    def get_queryset(self):
        kwargs = self.request.session['kwargs']
        return Protocolo.objects.filter(
            **kwargs)


class ProtocoloPesquisaView(FormMixin, GenericView):
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

            request.session['kwargs'] = kwargs
            return redirect('protocolo_list')
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


class AnularProtocoloAdmView(FormMixin, GenericView):
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
            justificativa_anulacao = sub('&nbsp;', ' ', strip_tags(
                request.POST['justificativa_anulacao']))
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


class ProtocoloDocumentForm(forms.Form):

    NUMERACAO_CHOICES = [('1', 'Sequencial por Ano'),
                         ('2', 'Sequencial Único')]

    numeracao = forms.ChoiceField(required=True,
                                  choices=NUMERACAO_CHOICES,
                                  widget=forms.RadioSelect(
                                      renderer=HorizontalRadioRenderer),
                                  label='')

    tipo_protocolo = forms.ChoiceField(required=True,
                                       label='Tipo de Protocolo',
                                       choices=TIPOS_PROTOCOLO[1:],
                                       widget=forms.RadioSelect(
                                           renderer=HorizontalRadioRenderer))
    tipo_documento = forms.ChoiceField(required=True,
                                       label='Tipo de Documento',
                                       choices=get_tipos_documento(),
                                       widget=forms.Select(
                                           attrs={'class': 'selector'}))
    num_paginas = forms.CharField(label='Núm. Páginas', required=True)
    assunto = forms.CharField(
        widget=forms.Textarea, label='Assunto', required=True)

    interessado = forms.CharField(required=True,
                                  label='Interessado')

    observacao = forms.CharField(required=True,
                                 widget=forms.Textarea, label='Observação')


class ProtocoloDocumentoView(FormMixin, GenericView):

    template_name = "protocoloadm/protocolar_documento.html"
    model = Protocolo

    def get_success_url(self):
        return reverse('protocolar_doc')

    def get(self, request, *args, **kwargs):
        form = ProtocoloDocumentForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):

        form = ProtocoloDocumentForm(request.POST)

        if form.is_valid():

            if request.POST['numeracao'] == '1':
                numeracao = Protocolo.objects.filter(
                    ano=date.today().year).aggregate(Max('numero'))
            else:
                numeracao = Protocolo.objects.all().aggregate(Max('numero'))

            protocolo = Protocolo()

            protocolo.numero = numeracao['numero__max'] + 1
            protocolo.ano = datetime.now().year
            protocolo.data = datetime.now().strftime("%Y-%m-%d")
            protocolo.hora = datetime.now().strftime("%H:%M")
            protocolo.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            protocolo.tipo_protocolo = request.POST['tipo_protocolo']
            protocolo.tipo_processo = '0'  # TODO validar o significado
            protocolo.interessado = request.POST['interessado']
            protocolo.anulado = False
            protocolo.tipo_documento = TipoDocumentoAdministrativo.objects.get(
                id=request.POST['tipo_documento'])
            protocolo.assunto_ementa = sub(
                '&nbsp;', ' ', strip_tags(request.POST['assunto']))
            protocolo.numero_paginas = request.POST['num_paginas']
            protocolo.observacao = sub(
                '&nbsp;', ' ', strip_tags(request.POST['observacao']))

            protocolo.save()

            message = "Protocolo criado com sucesso"
            return render(request,
                          reverse('protocolo'),
                          {'form': form, 'message': message})
        else:
            return self.form_invalid(form)


class ProtocoloMateriaForm(forms.Form):

    NUMERACAO_CHOICES = [('1', 'Sequencial por Ano'),
                         ('2', 'Sequencial Único')]

    numeracao = forms.ChoiceField(required=True,
                                  choices=NUMERACAO_CHOICES,
                                  widget=forms.RadioSelect(
                                      renderer=HorizontalRadioRenderer),
                                  label='')

    tipo_protocolo = forms.ChoiceField(required=True,
                                       label='Tipo de Protocolo',
                                       choices=TIPOS_PROTOCOLO[1:],
                                       widget=forms.RadioSelect(
                                           renderer=HorizontalRadioRenderer))

    tipo_materia = forms.ChoiceField(required=False,
                                     label='Tipo Matéria',
                                     choices=get_tipos_materia(),
                                     widget=forms.Select(
                                         attrs={'class': 'selector'}))
    num_paginas = forms.CharField(label='Núm. Páginas', required=True)
    ementa = forms.CharField(
        widget=forms.Textarea, label='Ementa', required=True)
    autor = forms.CharField(label='Autor', required=True)
    observacao = forms.CharField(required=True,
                                 widget=forms.Textarea,
                                 label='Observação')


class ProtocoloMateriaView(FormMixin, GenericView):

    template_name = "protocoloadm/protocolar_materia.html"
    model = Protocolo

    def get(self, request, *args, **kwargs):
        form = ProtocoloMateriaForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):

        form = ProtocoloMateriaForm(request.POST)

        if form.is_valid():

            if request.POST['numeracao'] == '1':
                numeracao = Protocolo.objects.filter(
                    ano=date.today().year).aggregate(Max('numero'))
            else:
                numeracao = Protocolo.objects.all().aggregate(Max('numero'))

            protocolo = Protocolo()

            protocolo.numero = numeracao['numero__max'] + 1
            protocolo.ano = datetime.now().year
            protocolo.data = datetime.now().strftime("%Y-%m-%d")
            protocolo.hora = datetime.now().strftime("%H:%M")
            protocolo.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            protocolo.tipo_protocolo = request.POST['tipo_protocolo']
            protocolo.tipo_processo = '0'  # TODO validar o significado
            protocolo.autor = Autor.objects.get(id=request.POST['autor'])
            protocolo.anulado = False
            protocolo.tipo_materia = TipoMateriaLegislativa.objects.get(
                id=request.POST['tipo_materia'])
            protocolo.numero_paginas = request.POST['num_paginas']
            protocolo.observacao = sub(
                '&nbsp;', ' ', strip_tags(request.POST['observacao']))

            protocolo.save()

            message = "Protocolo criado com sucesso"
            return render(request,
                          reverse('protocolo'),
                          {'form': form, 'message': message})
        else:
            return self.form_invalid(form)

# TODO: move to Proposicao app


class ProposicaoReceberView(TemplateView):
    template_name = "protocoloadm/proposicao_receber.html"


class ProposicoesNaoRecebidasView(ListView):
    template_name = "protocoloadm/proposicoes_naorecebidas.html"
    model = Proposicao
    paginate_by = 10

    def get_queryset(self):
        return Proposicao.objects.filter(data_envio__isnull=False, status='E')


class ProposicoesNaoIncorporadasView(ListView):
    template_name = "protocoloadm/proposicoes_naoincorporadas.html"
    model = Proposicao
    paginate_by = 10

    def get_queryset(self):
        return Proposicao.objects.filter(data_envio__isnull=False,
                                         data_devolucao__isnull=False,
                                         status='D')


class ProposicoesIncorporadasView(ListView):
    template_name = "protocoloadm/proposicoes_incorporadas.html"
    model = Proposicao
    paginate_by = 10

    def get_queryset(self):
        return Proposicao.objects.filter(data_envio__isnull=False,
                                         data_recebimento__isnull=False,
                                         status='I')


class ProposicaoSimpleForm(forms.Form):

    tipo = forms.CharField(label='Tipo',
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    materia = forms.CharField(label='Matéria',
                              widget=forms.TextInput(
                                  attrs={'readonly': 'readonly'}))
    data_envio = forms.DateField(label='Data Envio',
                                 widget=forms.DateInput(
                                     format='%d/%m/%Y',
                                     attrs={'readonly': 'readonly'}))
    data_recebimento = forms.DateField(label='Data Recebimento',
                                       widget=forms.DateInput(
                                           format='%d/%m/%Y',
                                           attrs={'readonly': 'readonly'}))

    descricao = forms.CharField(label='Descrição',
                                widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}))

    numero_proposicao = forms.CharField(label='Número',
                                        widget=forms.TextInput(
                                            attrs={'readonly': 'readonly'}))
    # ano = forms.CharField(label='Ano',
    #                             widget = forms.TextInput(
    #                               attrs={'readonly':'readonly'}))


class ProposicaoView(DetailView):
    template_name = "protocoloadm/proposicao_view.html"
    model = Proposicao

    def get(self, request, *args, **kwargs):
        proposicao = Proposicao.objects.get(id=kwargs['pk'])
        data = {  # 'ano': proposicao.ano, # TODO: FIX
            'tipo': proposicao.tipo.descricao,  # TODO: FIX
            'materia': proposicao.materia,
            'numero_proposicao': proposicao.numero_proposicao,
            'data_envio': proposicao.data_envio,
            'data_recebimento': proposicao.data_recebimento,
            'descricao': proposicao.descricao}
        form = ProposicaoSimpleForm(initial=data)
        return self.render_to_response({'form': form})

    def get_context_data(self, **kwargs):
        context = super(ProposicaoView, self).get_context_data(**kwargs)
        context['form'] = ProposicaoSimpleForm
        return context

# class PesquisaDocForm(forms.Form):


class PesquisarDocumentoAdministrativo(TemplateView):
    template_name = "protocoloadm/pesquisa_doc_adm.html"

    def get_tipos_doc(self):
        return TipoDocumentoAdministrativo.objects.all()

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            {"tipos_doc": TipoDocumentoAdministrativo.objects.all()}
        )

    def post(self, request, *args, **kwargs):

        if request.POST['tipo_documento']:
            kwargs['tipo_id'] = request.POST['tipo_documento']

        if request.POST['numero']:
            kwargs['numero'] = request.POST['numero']

        if request.POST['ano']:
            kwargs['ano'] = request.POST['ano']

        if request.POST['numero_protocolo']:
            kwargs['numero_protocolo'] = request.POST['numero_protocolo']

        if request.POST['periodo_inicial']:
            kwargs['periodo_inicial'] = request.POST['periodo_inicial']

        if request.POST['periodo_final']:
            kwargs['periodo_final'] = request.POST['periodo_final']

        if request.POST['interessado']:
            kwargs['interessado'] = request.POST['interessado']

        if request.POST['assunto']:
            kwargs['assunto'] = request.POST['assunto']

        if request.POST['tramitacao']:
            if request.POST['tramitacao'] == 1:
                kwargs['tramitacao'] = True
            elif request.POST['tramitacao'] == 0:
                kwargs['tramitacao'] = False
            else:
                kwargs['tramitacao'] = request.POST['tramitacao']

        # TODO
        # if request.POST['localizacao']:
        #     kwargs['localizacao'] = request.POST['localizacao']

        # if request.POST['situacao']:
        #     kwargs['situacao'] = request.POST['situacao']

        doc = DocumentoAdministrativo.objects.filter(**kwargs)

        if len(doc) == 0:
            return self.render_to_response(
                {'error': 'Nenhum resultado encontrado!',
                    "tipos_doc": TipoDocumentoAdministrativo.objects.all()}
            )
        else:
            return self.render_to_response(
                {'documentos': doc}
            )


class DetailDocumentoAdministrativo(DetailView):
    template_name = "protocoloadm/detail_doc_adm.html"

    def get_tipos_doc(self):
        return TipoDocumentoAdministrativo.objects.all()

    def get(self, request, *args, **kwargs):
        doc = DocumentoAdministrativo.objects.get(id=kwargs['pk'])
        return self.render_to_response({
            'doc': doc,
            'tipos_doc': TipoDocumentoAdministrativo.objects.all()
        })

    def post(self, request, *args, **kwargs):

        if 'Salvar' in request.POST:
            documento = DocumentoAdministrativo.objects.get(id=kwargs['pk'])

            if request.POST['numero']:
                documento.numero = request.POST['numero']

            if request.POST['ano']:
                documento.ano = request.POST['ano']

            if request.POST['data']:
                documento.data = datetime.strptime(
                    request.POST['data'], "%d/%m/%Y")

            if request.POST['numero_protocolo']:
                documento.numero_protocolo = request.POST['numero_protocolo']

            if request.POST['assunto']:
                documento.assunto = request.POST['assunto']

            if request.POST['interessado']:
                documento.interessado = request.POST['interessado']

            if request.POST['tramitacao']:
                documento.tramitacao = request.POST['tramitacao']

            if request.POST['dias_prazo']:
                documento.dias_prazo = request.POST['dias_prazo']

            if request.POST['data_fim_prazo']:
                documento.data_fim_prazo = datetime.strptime(
                    request.POST['data_fim_prazo'], "%d/%m/%Y")

            if request.POST['observacao']:
                documento.observacao = request.POST['observacao']

            documento.save()
        elif 'Excluir' in request.POST:
            DocumentoAdministrativo.objects.get(
                id=kwargs['pk']).delete()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('pesq_doc_adm')


class ModelFormDocumentoAcessorioAdministrativo(ModelForm):

    data = forms.DateField(label=u'Data', input_formats=['%d/%m/%Y'],
                           required=False,
                           widget=forms.DateInput(format='%d/%m/%Y'))

    class Meta:
        model = DocumentoAcessorioAdministrativo
        fields = ['tipo',
                  'nome',
                  'data',
                  'autor',
                  'arquivo',
                  'assunto']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Incluir Documento Acessório',
                'tipo',
                'nome',
                'data',
                'autor',
                'arquivo',
                'assunto',
                ButtonHolder(
                    Submit('submit', 'Salvar',
                           css_class='button primary')
                )
            )
        )
        super(ModelFormDocumentoAcessorioAdministrativo, self).__init__(
            *args, **kwargs)


class DocumentoAcessorioAdministrativoView(FormMixin, GenericView):
    template_name = "protocoloadm/documento_acessorio_administrativo.html"

    def get(self, request, *args, **kwargs):
        form = ModelFormDocumentoAcessorioAdministrativo()
        doc = DocumentoAdministrativo.objects.get(
            id=kwargs['pk'])
        doc_ace_null = ''
        try:
            doc_acessorio = DocumentoAcessorioAdministrativo.objects.filter(
                documento_id=kwargs['pk'])
        except ObjectDoesNotExist:
            doc_ace_null = 'Nenhum documento acessório \
                 cadastrado para este processo.'

        return self.render_to_response({'doc': doc,
                                        'doc_ace': doc_acessorio,
                                        'doc_ace_null': doc_ace_null,
                                        'form': form})

    def post(self, request, *args, **kwargs):
        form = ModelFormDocumentoAcessorioAdministrativo(request.POST)
        if form.is_valid():
            doc_acessorio = DocumentoAcessorioAdministrativo()
            doc_acessorio.tipo = form.cleaned_data['tipo']
            doc_acessorio.nome = form.cleaned_data['nome']
            doc_acessorio.data = form.cleaned_data['data']
            doc_acessorio.autor = form.cleaned_data['autor']
            doc_acessorio.assunto = form.cleaned_data['assunto']
            doc_acessorio.arquivo = form.cleaned_data['arquivo']
            doc_acessorio.documento = DocumentoAdministrativo.objects.get(
                id=kwargs['pk'])
            doc_acessorio.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('doc_ace_adm', kwargs={'pk': pk})


class TramitacaoAdmView(FormMixin, GenericView):
    template_name = "protocoloadm/tramitacao.html"

    def get(self, request, *args, **kwargs):

        pk = kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)
        tramitacoes = TramitacaoAdministrativo.objects.filter(
            documento=documento).order_by('-data_tramitacao')

        return self.render_to_response({'documento': documento,
                                        'tramitacoes': tramitacoes})


class TramitacaoAdmForm(ModelForm):

    data_tramitacao = forms.DateField(label=u'Data Tramitação',
                                      input_formats=['%d/%m/%Y'],
                                      required=False,
                                      widget=forms.DateInput(
                                          format='%d/%m/%Y',
                                          attrs={'class': 'dateinput'}))

    data_encaminhamento = forms.DateField(label=u'Data Encaminhamento',
                                          input_formats=['%d/%m/%Y'],
                                          required=False,
                                          widget=forms.DateInput(
                                              format='%d/%m/%Y',
                                              attrs={'class': 'dateinput'}))

    data_fim_prazo = forms.DateField(label=u'Data Fim Prazo',
                                     input_formats=['%d/%m/%Y'],
                                     required=False,
                                     widget=forms.DateInput(
                                         format='%d/%m/%Y',
                                         attrs={'class': 'dateinput'}))

    class Meta:
        model = TramitacaoAdministrativo
        fields = ['data_tramitacao',
                  'unidade_tramitacao_local',
                  'status',
                  'unidade_tramitacao_destino',
                  'data_encaminhamento',
                  'data_fim_prazo',
                  'texto',
                  'documento',
                  ]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Incluir Tramitação',
                     'data_tramitacao',
                     'unidade_tramitacao_local',
                     'status',
                     'unidade_tramitacao_destino',
                     'data_encaminhamento',
                     'data_fim_prazo',
                     'texto'),
            Field('documento', type="hidden"),
            ButtonHolder(
                Submit('submit', 'Salvar',
                       css_class='button primary')
            )
        )
        super(TramitacaoAdmForm, self).__init__(
            *args, **kwargs)


class TramitacaoAdmIncluirView(FormMixin, GenericView):
    template_name = "protocoloadm/tramitacao_incluir.html"

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)
        data = {'documento': documento}
        form = TramitacaoAdmForm(initial=data)

        return self.render_to_response({'documento': documento, 'form': form})

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        form = TramitacaoAdmForm(request.POST or None)

        if form.is_valid():
            tramitacao = form.save(commit=False)
            tramitacao.ultima = False
            tramitacao.save()
            return HttpResponseRedirect(
                reverse('tramitacao', kwargs={'pk': pk}))
        else:
            return self.form_invalid(form)


class TramitacaoAdmEditView(FormMixin, GenericView):

    template_name = "protocoloadm/tramitacao_edit.html"

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        tramitacao = TramitacaoAdministrativo.objects.get(id=pk)
        documento = tramitacao.documento
        form = TramitacaoAdmForm(instance=tramitacao)

        return self.render_to_response({'documento': documento, 'form': form})

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        print(kwargs)
        tramitacao = TramitacaoAdministrativo.objects.get(id=pk)
        form = TramitacaoAdmForm(request.POST, instance=tramitacao)

        if form.is_valid():
            tramitacao = form.save(commit=False)
            tramitacao.ultima = False
            tramitacao.save()
            return HttpResponseRedirect(
                reverse('tramitacao', kwargs={'pk': tramitacao.documento.id}))
        else:
            return self.form_invalid(form)


class TramitacaoAdmDeleteView(FormMixin, GenericView):

    template_name = "protocoloadm/tramitacao.html"

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        oid = kwargs['oid']

        documento = DocumentoAdministrativo.objects.get(id=pk)

        tramitacao = TramitacaoAdministrativo.objects.get(id=oid)
        tramitacao.delete()
        tramitacoes = TramitacaoAdministrativo.objects.filter(
            documento=documento)

        return self.render_to_response({'documento': documento,
                                        'tramitacoes': tramitacoes})
