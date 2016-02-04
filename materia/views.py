from datetime import date, datetime
from re import sub

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Fieldset, Layout
from django import forms
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from vanilla.views import GenericView

import sapl
from sapl.layout import form_actions
from comissoes.models import Comissao, Composicao
from compilacao.views import IntegracaoTaView
from norma.models import LegislacaoCitada, NormaJuridica, TipoNormaJuridica
from parlamentares.models import Parlamentar
from sapl.crud import build_crud
from sessao.models import AcompanharMateria

from .models import (Anexada, Autor, Autoria, DespachoInicial,
                     DocumentoAcessorio, MateriaLegislativa, Numeracao, Orgao,
                     Origem, Proposicao, RegimeTramitacao, Relatoria,
                     StatusTramitacao, TipoAutor, TipoDocumento,
                     TipoFimRelatoria, TipoMateriaLegislativa, TipoProposicao,
                     Tramitacao, UnidadeTramitacao)


origem_crud = build_crud(
    Origem, 'origem', [

        [_('Origem'),
         [('nome', 8), ('sigla', 4)]],
    ])

tipo_materia_crud = build_crud(
    TipoMateriaLegislativa, 'tipo_materia_legislativa', [

        [_('Tipo Matéria Legislativa'),
         [('sigla', 4), ('descricao', 8)]],
    ])

regime_tramitacao_crud = build_crud(
    RegimeTramitacao, 'regime_tramitacao', [

        [_('Tipo de Documento'),
         [('descricao', 12)]],
    ])

tipo_documento_crud = build_crud(
    TipoDocumento, 'tipo_documento', [

        [_('Regime Tramitação'),
         [('descricao', 12)]],
    ])

tipo_fim_relatoria_crud = build_crud(
    TipoFimRelatoria, 'fim_relatoria', [

        [_('Tipo Fim de Relatoria'),
         [('descricao', 12)]],
    ])

materia_legislativa_crud = build_crud(
    MateriaLegislativa, '', [

        [_('Identificação Básica'),
         [('tipo', 4), ('numero', 4), ('ano', 4)],
            [('data_apresentacao', 4),
             ('numero_protocolo', 4),
             ('tipo_apresentacao', 4)],
         [('texto_original', 12)]],

        [_('Outras Informações'),
         [('apelido', 4), ('dias_prazo', 4), ('polemica', 4)],
            [('objeto', 4), ('regime_tramitacao', 4), ('em_tramitacao', 4)],
            [('data_fim_prazo', 4),
             ('data_publicacao', 4),
             ('complementar', 4)]],

        [_('Origem Externa'),
         [('tipo_origem_externa', 4),
            ('numero_origem_externa', 4),
            ('ano_origem_externa', 4)],
            [('local_origem_externa', 6), ('data_origem_externa', 6)]],

        [_('Dados Textuais'),
         [('ementa', 12)],
            [('indexacao', 12)],
            [('observacao', 12)]],
    ])

Anexada_crud = build_crud(
    Anexada, '', [

        [_('Matéria Legislativa'),
         [('tip_id_basica_FIXME', 4),
            ('num_ident_basica_FIXME', 4),
            ('ano_ident_basica_FIXME', 4)],
            [('data_anexacao', 6), ('data_desanexacao', 6)]],

        [_('Matéria Anexada'),
         [('tip_id_basica_FIXME', 4),
            ('num_ident_basica_FIXME', 4),
            ('ano_ident_basica_FIXME', 4)],
            [('data_anexacao', 6), ('data_desanexacao', 6)]],
    ])

tipo_autor_crud = build_crud(
    TipoAutor, 'tipo_autor', [

        [_('Tipo Autor'),
         [('descricao', 12)]],
    ])

autor_crud = build_crud(
    Autor, 'autor', [

        [_('Autor'),
         [('tipo', 3), ('nome', 9)],
            [('username', 12)]],
    ])

autoria_crud = build_crud(
    Autoria, '', [

        [_('Autoria'),
         [('tip_autor_FIXME', 4),
            ('nom_autor_FIXME', 4),
            ('primeiro_autor', 4)]],
    ])

documento_acessorio_crud = build_crud(
    DocumentoAcessorio, '', [

        [_('Documento Acessório'),
         [('tipo', 6), ('nome', 6)],
            [('data', 6), ('autor', 6)],
            [('nom_arquivo_FIXME', 12)],
            [('ementa', 12)],
            [('txt_observacao_FIXME', 12)]],
    ])

numeracao_crud = build_crud(
    Numeracao, '', [

        [_('Numeração'),
         [('tipo_materia', 6), ('numero_materia', 6)],
            [('ano_materia', 6), ('data_materia', 6)]],
    ])

orgao_crud = build_crud(
    Orgao, 'orgao', [

        [_('Órgão'),
         [('nome', 4),
            ('sigla', 2),
            ('telefone', 2),
            ('endereco', 2),
            ('unidade_deliberativa', 2)]],
    ])

relatoria_crud = build_crud(
    Relatoria, '', [

        [_('Relatoria'),
         [('data_designacao_relator', 12)],
            [('dados_FIXME', 12)],
            [('data_destituicao_relator', 6), ('tipo_fim_relatoria', 6)]],
    ])

tipo_proposicao_crud = build_crud(
    TipoProposicao, 'tipo_proposicao', [

        [_('Tipo Proposição'),
         [('descricao', 12)],
            [('materia_ou_documento', 6), ('tipo_documento', 6)],
            [('modelo', 12)]],
    ])

proposicao_crud = build_crud(
    Proposicao, '', [

        [_('Proposição'),
         [('tipo', 4), ('dat_criacao_FIXME', 4), ('data_recebimento', 4)],
            [('descricao_FIXME', 12)],
            [('tip_id_basica_FIXME', 4),
             ('num_ident_basica_FIXME', 4),
             ('ano_ident_basica_FIXME', 4)],
            [('nom_arquivo_FIXME', 6), ('modelo_FIXME', 6)]],
    ])

status_tramitacao_crud = build_crud(
    StatusTramitacao, 'status_tramitacao', [

        [_('Status Tramitação'),
         [('indicador', 3),
            ('sigla', 2),
            ('descricao', 7)]],
    ])

unidade_tramitacao_crud = build_crud(
    UnidadeTramitacao, 'unidade_tramitacao', [

        [_('Unidade Tramitação'),
         [('orgao', 12)],
            [('comissao', 12)],
            [('parlamentar', 12)]],
    ])

tramitacao_crud = build_crud(
    Tramitacao, '', [

        [_('Tramitação'),
         [('cod_ult_tram_dest_FIXME', 6), ('unidade_tramitacao_local', 6)],
            [('status', 4), ('turno', 4), ('urgente', 4)],
            [('unidade_tramitacao_destino', 4),
             ('data_encaminhamento', 4),
             ('data_fim_prazo', 4)],
            [('texto', 12)]],
    ])


def get_range_anos():
    return [('', 'Selecione')] \
        + [(year, year) for year in range(date.today().year, 1960, -1)]


def get_regimes_tramitacao():
    return [('1', 'Normal'),
            ('3', 'Urgência'),
            ('4', 'Urgência Especial')]


def get_local_origem():
    return [('E', 'Poder Executivo'),
            ('L', 'Poder Legislativo')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class FormularioSimplificadoForm(ModelForm):

    data_apresentacao = forms.DateField(label=u'Data Apresentação',
                                        input_formats=['%d/%m/%Y'],
                                        required=False,
                                        widget=forms.DateInput(
                                            format='%d/%m/%Y'))

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data_apresentacao',
                  'numero_protocolo',
                  'regime_tramitacao',
                  'em_tramitacao',
                  'ementa',
                  'texto_original']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])

        row2 = sapl.layout.to_row(
            [('data_apresentacao', 4),
             ('numero_protocolo', 4),
             ('regime_tramitacao', 4)])

        row3 = sapl.layout.to_row(
            [('texto_original', 9),
             ('em_tramitacao', 3)])

        row4 = sapl.layout.to_row(
            [('ementa', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Formulário Simplificado',
                Fieldset(
                    'Identificação Básica',
                    row1, row2, row3, row4
                ),
                form_actions()
            )
        )
        super(FormularioSimplificadoForm, self).__init__(*args, **kwargs)


class FormularioCadastroForm(ModelForm):

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data_apresentacao',
                  'numero_protocolo',
                  'tipo_apresentacao',
                  'texto_original',
                  'apelido',
                  'dias_prazo',
                  'polemica',
                  'objeto',
                  'regime_tramitacao',
                  'em_tramitacao',
                  'data_fim_prazo',
                  'data_publicacao',
                  'complementar',
                  'tipo_origem_externa',
                  'numero_origem_externa',
                  'ano_origem_externa',
                  'local_origem_externa',
                  'data_origem_externa',
                  'ementa',
                  'indexacao',
                  'observacao']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Formulário de Cadastro',
                Fieldset(
                    'Identificação Básica',
                    'tipo',
                    'numero',
                    'ano',
                    'data_apresentacao',
                    'numero_protocolo',
                    'tipo_apresentacao',
                    'texto_original'
                ),
                Fieldset(
                    'Outras Informações',
                    'apelido',
                    'dias_prazo',
                    'polemica',
                    'objeto',
                    'regime_tramitacao',
                    'em_tramitacao',
                    'data_fim_prazo',
                    'data_publicacao',
                    'complementar'
                ),
                Fieldset(
                    'Origem Externa',
                    'tipo_origem_externa',
                    'numero_origem_externa',
                    'ano_origem_externa',
                    'local_origem_externa',
                    'data_origem_externa'
                ),
                Fieldset(
                    'Dados Textuais',
                    'ementa',
                    'indexacao',
                    'observacao'
                ),
                form_actions()
            )
        )
        super(FormularioCadastroForm, self).__init__(*args, **kwargs)


class FormularioSimplificadoView(FormMixin, GenericView):
    template_name = "materia/formulario_simplificado.html"

    def get_success_url(self):
        return reverse('materialegislativa:list')

    def get(self, request, *args, **kwargs):
        form = FormularioSimplificadoForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = FormularioSimplificadoForm(request.POST)

        if form.is_valid:
            materia = form.save(commit=False)
            if 'texto_original' in request.FILES:
                materia.texto_original = request.FILES['texto_original']
            materia.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

        return self.render_to_response({'form': form})


class FormularioCadastroView(FormMixin, GenericView):
    template_name = "materia/formulario_cadastro.html"

    def get(self, request, *args, **kwargs):
        form = FormularioCadastroForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = FormularioCadastroForm(request.POST)
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('formulario_cadastro')


class MateriaAnexadaForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label='Tipo',
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero = forms.CharField(label='Número', required=True)

    ano = forms.CharField(label='Ano', required=True)

    data_anexacao = forms.DateField(label='Data Anexação',
                                    required=True,
                                    input_formats=['%d/%m/%Y'],
                                    widget=forms.TextInput(
                                        attrs={'class': 'dateinput'}))

    data_desanexacao = forms.DateField(label='Data Desanexação',
                                       required=False,
                                       input_formats=['%d/%m/%Y'],
                                       widget=forms.TextInput(
                                           attrs={'class': 'dateinput'}))

    class Meta:
        model = Anexada
        fields = ['tipo', 'data_anexacao', 'data_desanexacao']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])
        row2 = sapl.layout.to_row(
            [('data_anexacao', 6),
             ('data_desanexacao', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Anexar Matéria',
                row1, row2,
                form_actions()
            )
        )
        super(MateriaAnexadaForm, self).__init__(
            *args, **kwargs)


class MateriaAnexadaView(FormMixin, GenericView):
    template_name = "materia/materia_anexada.html"

    def get(self, request, *args, **kwargs):
        form = MateriaAnexadaForm()
        materia = MateriaLegislativa.objects.get(
            id=kwargs['pk'])
        anexadas = Anexada.objects.filter(
            materia_principal_id=kwargs['pk'])

        return self.render_to_response({'object': materia,
                                        'anexadas': anexadas,
                                        'form': form})

    def post(self, request, *args, **kwargs):
        form = MateriaAnexadaForm(request.POST)
        anexadas = Anexada.objects.filter(
            materia_principal_id=kwargs['pk'])
        mat_principal = MateriaLegislativa.objects.get(
            id=kwargs['pk'])

        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            numero = form.cleaned_data['numero']
            ano = form.cleaned_data['ano']
            data_anexacao = form.cleaned_data['data_anexacao']

            if 'data_desanexacao' in request.POST:
                data_desanexacao = form.cleaned_data['data_desanexacao']

            try:
                mat_anexada = MateriaLegislativa.objects.get(
                    numero=numero, ano=ano, tipo=tipo)

                if mat_principal.tipo == mat_anexada.tipo:

                    msg = 'A matéria a ser anexada não pode ser do mesmo \
                            tipo da matéria principal.'
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'form': form,
                         'materialegislativa': mat_principal,
                         'anexadas': anexadas})

                anexada = Anexada()
                anexada.materia_principal = mat_principal
                anexada.materia_anexada = mat_anexada
                anexada.data_anexacao = data_anexacao

                if data_desanexacao:
                    anexada.data_desanexacao = data_desanexacao

                anexada.save()

            except ObjectDoesNotExist:
                msg = 'A matéria a ser anexada não existe no cadastro \
                        de matérias legislativas.'
                messages.add_message(request, messages.INFO, msg)
                return self.render_to_response(
                    {'form': form,
                     'materialegislativa': mat_principal,
                     'anexadas': anexadas})

            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'materialegislativa': mat_principal,
                 'anexadas': anexadas})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia_anexada', kwargs={'pk': pk})


class MateriaAnexadaEditView(FormMixin, GenericView):
    template_name = "materia/materia_anexada_edit.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        anexada = Anexada.objects.get(id=kwargs['id'])

        data = {}
        data['tipo'] = anexada.materia_anexada.tipo
        data['numero'] = anexada.materia_anexada.numero
        data['ano'] = anexada.materia_anexada.ano
        data['data_anexacao'] = anexada.data_anexacao
        data['data_desanexacao'] = anexada.data_desanexacao

        form = MateriaAnexadaForm(initial=data)

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'data': data,
             'get_tipos_materia': TipoMateriaLegislativa.objects.all()})

    def post(self, request, *args, **kwargs):

        form = MateriaAnexadaForm(request.POST)
        anexada = Anexada.objects.get(id=kwargs['id'])
        mat_principal = MateriaLegislativa.objects.get(
            id=kwargs['pk'])

        if form.is_valid():
            if 'excluir' in request.POST:
                anexada.delete()
                return self.form_valid(form)
            elif 'salvar' in request.POST:

                tipo = form.cleaned_data['tipo']
                numero = form.cleaned_data['numero']
                ano = form.cleaned_data['ano']
                data_anexacao = form.cleaned_data['data_anexacao']

                if 'data_desanexacao' in request.POST:
                    data_desanexacao = form.cleaned_data['data_desanexacao']

                try:
                    mat_anexada = MateriaLegislativa.objects.get(
                        numero=numero, ano=ano, tipo=tipo)

                    if mat_principal.tipo == mat_anexada.tipo:

                        msg = 'A matéria a ser anexada não pode ser do mesmo \
                            tipo da matéria principal.'
                        messages.add_message(request, messages.INFO, msg)
                        return self.render_to_response(
                            {'form': form,
                             'materialegislativa': mat_principal
                             })

                    anexada.materia_principal = mat_principal
                    anexada.materia_anexada = mat_anexada
                    anexada.data_anexacao = data_anexacao

                    if data_desanexacao:
                        anexada.data_desanexacao = data_desanexacao

                    anexada.save()
                    return self.form_valid(form)

                except ObjectDoesNotExist:
                    msg = 'A matéria a ser anexada não existe no cadastro \
                        de matérias legislativas.'
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'form': form,
                         'materialegislativa': mat_principal})

        else:
            return self.render_to_response(
                {'form': form,
                 'materialegislativa': mat_principal})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia_anexada', kwargs={'pk': pk})


class DespachoInicialFom(ModelForm):

    class Meta:
        model = DespachoInicial
        fields = ['comissao']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Adicionar Despacho Inicial',
                'comissao',
                form_actions()
            )
        )
        super(DespachoInicialFom, self).__init__(*args, **kwargs)


class DespachoInicialView(FormMixin, GenericView):
    template_name = "materia/despacho_inicial.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.filter(materia_id=materia.id)
        form = DespachoInicialFom()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'despachos': despacho})

    def post(self, request, *args, **kwargs):
        form = DespachoInicialFom(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.filter(materia_id=materia.id)

        if form.is_valid():
            despacho = DespachoInicial()
            despacho.comissao = form.cleaned_data['comissao']
            despacho.materia = materia
            despacho.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'despachos': despacho})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('despacho_inicial', kwargs={'pk': pk})


class DespachoInicialEditView(FormMixin, GenericView):
    template_name = "materia/despacho_inicial_edit.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.get(id=kwargs['id'])
        form = DespachoInicialFom()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'despacho': despacho,
             'comissoes': Comissao.objects.all()})

    def post(self, request, *args, **kwargs):
        form = DespachoInicialFom(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.get(id=kwargs['id'])

        if form.is_valid():
            if 'excluir' in request.POST:
                despacho.delete()
                return self.form_valid(form)
            elif 'salvar' in request.POST:
                despacho.comissao = form.cleaned_data['comissao']
                despacho.materia = materia
                despacho.save()
                return self.form_valid(form)
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'despacho': despacho,
                 'comissoes': Comissao.objects.all()})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('despacho_inicial', kwargs={'pk': pk})


class LegislacaoCitadaForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label='Tipo Norma',
        required=True,
        queryset=TipoNormaJuridica.objects.all(),
        empty_label='Selecione',
    )

    numero = forms.CharField(label='Número', required=True)

    ano = forms.CharField(label='Ano', required=True)

    disposicao = forms.CharField(label='Disposição', required=False)

    parte = forms.CharField(label='Parte', required=False)

    livro = forms.CharField(label='Livro', required=False)

    titulo = forms.CharField(label='Título', required=False)

    capitulo = forms.CharField(label='Capítulo', required=False)

    secao = forms.CharField(label='Seção', required=False)

    subsecao = forms.CharField(label='Subseção', required=False)

    artigo = forms.CharField(label='Artigo', required=False)

    paragrafo = forms.CharField(label='Parágrafo', required=False)

    inciso = forms.CharField(label='Inciso', required=False)

    alinea = forms.CharField(label='Alínea', required=False)

    item = forms.CharField(label='Item', required=False)

    class Meta:
        model = LegislacaoCitada
        fields = ['tipo',
                  'numero',
                  'ano',
                  'disposicao',
                  'parte',
                  'livro',
                  'titulo',
                  'capitulo',
                  'secao',
                  'subsecao',
                  'artigo',
                  'paragrafo',
                  'inciso',
                  'alinea',
                  'item']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])

        row2 = sapl.layout.to_row(
            [('disposicao', 3),
             ('parte', 3),
             ('livro', 3),
             ('titulo', 3)])

        row3 = sapl.layout.to_row(
            [('capitulo', 3),
             ('secao', 3),
             ('subsecao', 3),
             ('artigo', 3)])

        row4 = sapl.layout.to_row(
            [('paragrafo', 3),
             ('inciso', 3),
             ('alinea', 3),
             ('item', 3)])

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Fieldset(
                'Incluir Legislação Citada',
                row1, row2, row3, row4,
                form_actions()
            )
        )
        super(LegislacaoCitadaForm, self).__init__(*args, **kwargs)


class LegislacaoCitadaView(FormMixin, GenericView):
    template_name = "materia/legislacao_citada.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao = LegislacaoCitada.objects.filter(materia_id=kwargs['pk'])
        form = LegislacaoCitadaForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'legislacao': legislacao})

    def post(self, request, *args, **kwargs):
        form = LegislacaoCitadaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao_list = LegislacaoCitada.objects.filter(
            materia_id=kwargs['pk'])

        if form.is_valid():
            legislacao = LegislacaoCitada()

            try:
                norma = NormaJuridica.objects.get(
                    tipo_id=form.cleaned_data['tipo'],
                    numero=form.cleaned_data['numero'],
                    ano=form.cleaned_data['ano'])
            except ObjectDoesNotExist:
                msg = 'Norma Juridica não existe.'
                messages.add_message(request, messages.INFO, msg)
                return self.render_to_response({'form': form,
                                                'object': materia,
                                                'legislacao': legislacao_list})
            legislacao.materia = materia
            legislacao.norma = norma
            legislacao.disposicoes = form.cleaned_data['disposicao']
            legislacao.parte = form.cleaned_data['parte']
            legislacao.livro = form.cleaned_data['livro']
            legislacao.titulo = form.cleaned_data['titulo']
            legislacao.capitulo = form.cleaned_data['capitulo']
            legislacao.secao = form.cleaned_data['secao']
            legislacao.subsecao = form.cleaned_data['subsecao']
            legislacao.artigo = form.cleaned_data['artigo']
            legislacao.paragrafo = form.cleaned_data['paragrafo']
            legislacao.inciso = form.cleaned_data['inciso']
            legislacao.alinea = form.cleaned_data['alinea']
            legislacao.item = form.cleaned_data['item']

            legislacao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'legislacao': legislacao_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('legislacao_citada', kwargs={'pk': pk})


class LegislacaoCitadaEditView(FormMixin, GenericView):
    template_name = "materia/legislacao_citada_edit.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('legislacao_citada', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao = LegislacaoCitada.objects.get(id=kwargs['id'])
        form = LegislacaoCitadaForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'legislacao': legislacao,
             'tipos_norma': TipoNormaJuridica.objects.all()})

    def post(self, request, *args, **kwargs):
        form = LegislacaoCitadaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao = LegislacaoCitada.objects.get(id=kwargs['id'])

        if form.is_valid():
            if 'excluir' in request.POST:
                legislacao.delete()
                return self.form_valid(form)
            elif 'salvar' in request.POST:
                try:
                    norma = NormaJuridica.objects.get(
                        tipo_id=form.cleaned_data['tipo'],
                        numero=form.cleaned_data['numero'],
                        ano=form.cleaned_data['ano'])
                except ObjectDoesNotExist:
                    msg = 'Norma Juridica não existe.'
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'form': form,
                         'object': materia,
                         'legislacao': legislacao,
                         'tipos_norma': TipoNormaJuridica.objects.all()})
                legislacao.materia = materia
                legislacao.norma = norma
                legislacao.disposicoes = form.cleaned_data['disposicao']
                legislacao.parte = form.cleaned_data['parte']
                legislacao.livro = form.cleaned_data['livro']
                legislacao.titulo = form.cleaned_data['titulo']
                legislacao.capitulo = form.cleaned_data['capitulo']
                legislacao.secao = form.cleaned_data['secao']
                legislacao.subsecao = form.cleaned_data['subsecao']
                legislacao.artigo = form.cleaned_data['artigo']
                legislacao.paragrafo = form.cleaned_data['paragrafo']
                legislacao.inciso = form.cleaned_data['inciso']
                legislacao.alinea = form.cleaned_data['alinea']
                legislacao.item = form.cleaned_data['item']

                legislacao.save()
                return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'object': materia})


class NumeracaoForm(ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label='Tipo de Matéria',
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    data_materia = forms.DateField(label='Data',
                                   required=False,
                                   input_formats=['%d/%m/%Y'],
                                   widget=forms.TextInput(
                                       attrs={'class': 'dateinput'}))

    ano_materia = forms.ChoiceField(required=True,
                                    label='Ano',
                                    choices=get_range_anos(),
                                    widget=forms.Select(
                                        attrs={'class': 'selector'}))

    numero_materia = forms.CharField(
        label='Número', required=True)

    class Meta:
        model = Numeracao
        fields = ['tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'data_materia']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo_materia', 12)])
        row2 = sapl.layout.to_row(
            [('numero_materia', 4),
             ('ano_materia', 4),
             ('data_materia', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Incluir Numeração',
                row1, row2,
                form_actions()
            )
        )
        super(NumeracaoForm, self).__init__(*args, **kwargs)


class NumeracaoView(FormMixin, GenericView):
    template_name = "materia/numeracao.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao = Numeracao.objects.filter(materia_id=kwargs['pk'])
        form = NumeracaoForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'numeracao': numeracao})

    def post(self, request, *args, **kwargs):
        form = NumeracaoForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao_list = Numeracao.objects.filter(
            materia_id=kwargs['pk'])

        if form.is_valid():
            numeracao = Numeracao()
            tipo = TipoMateriaLegislativa.objects.get(
                id=form.cleaned_data['tipo_materia'])

            numeracao.materia = materia
            numeracao.tipo_materia = tipo
            numeracao.numero_materia = form.cleaned_data['numero_materia']
            numeracao.ano_materia = form.cleaned_data['ano_materia']
            numeracao.data_materia = form.cleaned_data['data_materia']

            numeracao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'numeracao': numeracao_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('numeracao', kwargs={'pk': pk})


class NumeracaoEditView(FormMixin, GenericView):
    template_name = "materia/numeracao_edit.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao = Numeracao.objects.get(id=kwargs['id'])
        form = NumeracaoForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'numeracao': numeracao,
             'tipos': TipoMateriaLegislativa.objects.all()})

    def post(self, request, *args, **kwargs):
        form = NumeracaoForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao = Numeracao.objects.get(id=kwargs['id'])

        if form.is_valid():
            if 'excluir' in request.POST:
                numeracao.delete()
            elif 'salvar' in request.POST:
                tipo = TipoMateriaLegislativa.objects.get(
                    id=form.cleaned_data['tipo_materia'])

                numeracao.materia = materia
                numeracao.tipo_materia = tipo
                numeracao.numero_materia = form.cleaned_data['numero_materia']
                numeracao.ano_materia = form.cleaned_data['ano_materia']
                numeracao.data_materia = form.cleaned_data['data_materia']

                numeracao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'numeracao': numeracao})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('numeracao', kwargs={'pk': pk})


class DocumentoAcessorioForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label='Tipo',
        required=True,
        queryset=TipoDocumento.objects.all(),
        empty_label='Selecione',
    )

    data = forms.DateField(label='Data',
                           required=False,
                           input_formats=['%d/%m/%Y'],
                           widget=forms.TextInput(
                               attrs={'class': 'dateinput'}))

    nome = forms.CharField(
        label='Nome', required=True)

    autor = forms.CharField(
        label='Autor', required=True)

    ementa = forms.CharField(
        label='Ementa', required=True)

    class Meta:
        model = DocumentoAcessorio
        fields = ['tipo',
                  'nome',
                  'data',
                  'autor',
                  'ementa']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo', 4),
             ('nome', 4),
             ('data', 4)])

        row2 = sapl.layout.to_row(
            [('autor', 12)])

        row3 = sapl.layout.to_row(
            [('ementa', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Incluir Documento Acessório',
                row1, row2, row3,
                form_actions()
            )
        )
        super(DocumentoAcessorioForm, self).__init__(*args, **kwargs)


class DocumentoAcessorioView(FormMixin, GenericView):
    template_name = "materia/documento_acessorio.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        docs = DocumentoAcessorio.objects.filter(materia_id=kwargs['pk'])
        form = DocumentoAcessorioForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'docs': docs})

    def post(self, request, *args, **kwargs):
        form = DocumentoAcessorioForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        docs_list = DocumentoAcessorio.objects.filter(
            materia_id=kwargs['pk'])

        if form.is_valid():
            documento_acessorio = DocumentoAcessorio()
            tipo = TipoDocumento.objects.get(
                id=form.cleaned_data['tipo'])

            documento_acessorio.materia = materia
            documento_acessorio.tipo = tipo
            documento_acessorio.data = form.cleaned_data['data']
            documento_acessorio.nome = form.cleaned_data['nome']
            documento_acessorio.autor = form.cleaned_data['autor']
            documento_acessorio.ementa = form.cleaned_data['ementa']

            documento_acessorio.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'docs': docs_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('documento_acessorio', kwargs={'pk': pk})


class DocumentoAcessorioEditView(FormMixin, GenericView):
    template_name = "materia/documento_acessorio_edit.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        documento = DocumentoAcessorio.objects.get(id=kwargs['id'])
        form = DocumentoAcessorioForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'doc': documento,
             'tipos': TipoDocumento.objects.all()})

    def post(self, request, *args, **kwargs):
        form = DocumentoAcessorioForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        documento = DocumentoAcessorio.objects.get(id=kwargs['id'])

        if form.is_valid():
            if 'excluir' in request.POST:
                documento.delete()
            elif 'salvar' in request.POST:
                tipo = TipoDocumento.objects.get(
                    id=form.cleaned_data['tipo'])
                documento.materia = materia
                documento.tipo = tipo
                documento.data = form.cleaned_data['data']
                documento.nome = form.cleaned_data['nome']
                documento.autor = form.cleaned_data['autor']
                documento.ementa = form.cleaned_data['ementa']

                documento.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'doc': documento})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('documento_acessorio', kwargs={'pk': pk})


class RelatoriaForm(ModelForm):
    data_designacao_relator = forms.DateField(
        label=u'Data Designação',
        input_formats=['%d/%m/%Y'],
        required=False,
        widget=forms.DateInput(
            format='%d/%m/%Y',
            attrs={'class': 'dateinput'}))

    data_destituicao_relator = forms.DateField(
        label=u'Data Destituição',
        input_formats=['%d/%m/%Y'],
        required=False,
        widget=forms.DateInput(
            format='%d/%m/%Y',
            attrs={'class': 'dateinput'}))

    class Meta:
        model = Relatoria
        fields = ['data_designacao_relator',
                  'comissao',
                  'parlamentar',
                  'data_destituicao_relator',
                  'tipo_fim_relatoria'
                  ]


class RelatoriaEditView(FormMixin, GenericView):
    template_name = "materia/relatoria_edit.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('relatoria', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        form = RelatoriaForm()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        relatoria = Relatoria.objects.get(
            id=kwargs['id'])
        composicao = Composicao.objects.filter(
            comissao=relatoria.comissao).last()
        parlamentares = composicao.participacao_set.all()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'relatoria': relatoria,
             'tipo_fim_relatorias': TipoFimRelatoria.objects.all(),
             'parlamentares': parlamentares})

    def post(self, request, *args, **kwargs):
        form = RelatoriaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        relatoria = Relatoria.objects.get(id=kwargs['id'])
        composicao = Composicao.objects.filter(
            comissao=relatoria.comissao).last()
        parlamentares = composicao.participacao_set.all()

        if form.is_valid():
            if 'excluir' in request.POST:
                relatoria.delete()
                return self.form_valid(form)
            elif 'salvar' in request.POST:
                relatoria.materia = materia
                relatoria.comissao = relatoria.comissao
                relatoria.data_designacao_relator = form.cleaned_data[
                    'data_designacao_relator']
                relatoria.data_destituicao_relator = form.cleaned_data[
                    'data_destituicao_relator']
                relatoria.parlamentar = form.cleaned_data['parlamentar']
                relatoria.tipo_fim_relatoria = form.cleaned_data[
                    'tipo_fim_relatoria']
                relatoria.save()
                return self.form_valid(form)
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'relatoria': relatoria,
                 'tipo_fim_relatorias': TipoFimRelatoria.objects.all(),
                 'parlamentares': parlamentares})


class RelatoriaView(FormMixin, GenericView):
    template_name = "materia/relatoria.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('relatoria', kwargs={'pk': pk})

    def post(self, request, *args, **kwargs):
        form = RelatoriaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        relatorias = Relatoria.objects.filter(
            materia_id=kwargs['pk']).order_by('-data_designacao_relator')
        localizacao = Tramitacao.objects.filter(
            materia=materia).last()
        comissao = Comissao.objects.get(
            id=localizacao.unidade_tramitacao_destino_id)

        if form.is_valid():
            relatoria = form.save(commit=False)
            relatoria.materia = materia
            relatoria.comissao = comissao
            relatoria.save()
            return self.form_valid(form)
        else:

            composicao = Composicao.objects.get(comissao=comissao)
            parlamentares = composicao.participacao_set.all()

            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'relatorias': relatorias,
                 'comissao': comissao,
                 'tipo_fim_relatoria': TipoFimRelatoria.objects.all(),
                 'parlamentares': parlamentares})

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        relatorias = Relatoria.objects.filter(
            materia_id=kwargs['pk']).order_by('-data_designacao_relator')
        form = RelatoriaForm()

        localizacao = Tramitacao.objects.filter(
            materia=materia).last()

        try:
            comissao = Comissao.objects.get(
                id=localizacao.unidade_tramitacao_destino_id)
        except ObjectDoesNotExist:
            msg = 'O local atual deve  ser uma Comissão!'
            messages.add_message(request, messages.INFO, msg)
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'relatorias': relatorias})
        else:
            composicao = Composicao.objects.filter(comissao=comissao).last()
            parlamentares = composicao.participacao_set.all()
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'relatorias': relatorias,
                 'comissao': comissao,
                 'tipo_fim_relatoria': TipoFimRelatoria.objects.all(),
                 'parlamentares': parlamentares})


class TramitacaoForm(ModelForm):

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
        model = Tramitacao
        fields = ['data_tramitacao',
                  'unidade_tramitacao_local',
                  'status',
                  'turno',
                  'urgente',
                  'unidade_tramitacao_destino',
                  'data_encaminhamento',
                  'data_fim_prazo',
                  'texto']

    def __init__(self, *args, **kwargs):
        row1 = sapl.layout.to_row(
            [('data_tramitacao', 6),
             ('unidade_tramitacao_local', 6)])

        row2 = sapl.layout.to_row(
            [('status', 5),
             ('turno', 5),
             ('urgente', 2)])

        row3 = sapl.layout.to_row(
            [('unidade_tramitacao_destino', 12)])

        row4 = sapl.layout.to_row(
            [('data_encaminhamento', 6),
             ('data_fim_prazo', 6)])

        row5 = sapl.layout.to_row(
            [('texto', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Incluir Tramitação',
                     row1, row2, row3, row4, row5,
                     ),
            form_actions()
        )
        super(TramitacaoForm, self).__init__(
            *args, **kwargs)


class TramitacaoView(FormMixin, GenericView):
    template_name = "materia/tramitacao.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacoes = Tramitacao.objects.filter(
            materia_id=kwargs['pk']).order_by('-data_tramitacao')
        form = TramitacaoForm

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'tramitacoes': tramitacoes})

    def post(self, request, *args, **kwargs):
        form = TramitacaoForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacoes_list = Tramitacao.objects.filter(
            materia_id=kwargs['pk']).order_by('-data_tramitacao')

        if form.is_valid():
            ultima_tramitacao = Tramitacao.objects.filter(
                materia_id=kwargs['pk']).last()

            destino = ultima_tramitacao.unidade_tramitacao_destino
            cleaned_data = form.cleaned_data['unidade_tramitacao_local']
            if (destino == cleaned_data):
                tramitacao = form.save(commit=False)
                tramitacao.materia = materia
                tramitacao.save()
            else:
                msg = 'A origem da nova tramitação \
                        deve ser igual ao destino da última adicionada!'
                messages.add_message(request, messages.INFO, msg)
                return self.render_to_response(
                    {'form': form,
                     'object': materia,
                     'tramitacoes': tramitacoes_list})

            corpo_email = ('A tramitação da matéria %s foi alterada.' % materia
                           )
            destinatarios = AcompanharMateria.objects.values_list(
                'email', flat=True).filter(
                materia_cadastrada=materia)
            send_mail('Mudança de Tramitação',
                      corpo_email,
                      'sapl-test@interlegis.leg.br',
                      destinatarios,
                      fail_silently=True)
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'tramitacoes': tramitacoes_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('tramitacao_materia', kwargs={'pk': pk})


class TramitacaoEditView(FormMixin, GenericView):
    template_name = "materia/tramitacao_edit.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacao = Tramitacao.objects.get(id=kwargs['id'])
        form = TramitacaoForm

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'tramitacao': tramitacao,
             'turno': Tramitacao.TURNO_CHOICES,
             'status': StatusTramitacao.objects.all(),
             'unidade_tramitacao': UnidadeTramitacao.objects.all()})

    def post(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacao = Tramitacao.objects.get(id=kwargs['id'])
        form = TramitacaoForm(request.POST)

        if form.is_valid():
            if 'excluir' in request.POST:
                if tramitacao == Tramitacao.objects.filter(
                        materia=materia).last():
                    tramitacao.delete()
                    return self.form_valid(form)
                else:
                    msg = 'Somente a útlima tramitação pode ser\
                    deletada!'
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'object': materia,
                         'form': form,
                         'tramitacao': tramitacao,
                         'turno': Tramitacao.TURNO_CHOICES,
                         'status': StatusTramitacao.objects.all(),
                         'unidade_tramitacao': UnidadeTramitacao.objects.all()
                         })
            elif 'salvar' in request.POST:
                tramitacao.status = form.cleaned_data['status']
                tramitacao.turno = form.cleaned_data['turno']
                tramitacao.urgente = form.cleaned_data['urgente']
                tramitacao.unidade_tramitacao_destino = form.cleaned_data[
                    'unidade_tramitacao_destino']
                tramitacao.data_encaminhamento = form.cleaned_data[
                    'data_encaminhamento']
                tramitacao.data_fim_prazo = form.cleaned_data['data_fim_prazo']
                tramitacao.texto = form.cleaned_data['texto']

                tramitacao.save()
                return self.form_valid(form)
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'tramitacao': tramitacao,
                 'turno': Tramitacao.TURNO_CHOICES,
                 'status': StatusTramitacao.objects.all(),
                 'unidade_tramitacao': UnidadeTramitacao.objects.all()})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('tramitacao_materia', kwargs={'pk': pk})


class AutoriaForm(forms.Form):
    tipo_autor = forms.CharField()
    nome_autor = forms.CharField()
    primeiro_autor = forms.CharField()


class AutoriaView(GenericView):
    template_name = "materia/autoria.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        autorias = Autoria.objects.filter(materia=materia)
        form = AutoriaForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'autorias': autorias,
             'tipo_autores': TipoAutor.objects.all(),
             'autores': Autor.objects.all(),
             'tipo_autor_id': TipoAutor.objects.first().id})

    def post(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        autorias = Autoria.objects.filter(materia=materia)
        form = AutoriaForm(request.POST)

        if 'salvar' in request.POST:
            if int(form.data['primeiro_autor']) == 1:
                primeiro = True
            else:
                primeiro = False

            autor = Autor.objects.get(
                id=int(form.data['nome_autor']))

            try:
                autoria = Autoria.objects.get(
                    autor=autor,
                    materia=materia
                )
            except ObjectDoesNotExist:

                autoria = Autoria()
                autoria.autor = autor
                autoria.materia = materia
                autoria.primeiro_autor = primeiro
                autoria.save()

                return self.render_to_response(
                    {'object': materia,
                     'form': form,
                     'autorias': autorias,
                     'tipo_autores': TipoAutor.objects.all(),
                     'autores': Autor.objects.all(),
                     'tipo_autor_id': int(form.data['tipo_autor'])})
            else:
                msg = 'Essa autoria já foi adicionada!'
                messages.add_message(request, messages.INFO, msg)
                return self.render_to_response(
                    {'object': materia,
                     'form': form,
                     'autorias': autorias,
                     'tipo_autores': TipoAutor.objects.all(),
                     'autores': Autor.objects.all(),
                     'tipo_autor_id': int(form.data['tipo_autor'])})
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'autorias': autorias,
                 'tipo_autores': TipoAutor.objects.all(),
                 'autores': Autor.objects.all(),
                 'tipo_autor_id': int(form.data['tipo_autor'])})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('autoria', kwargs={'pk': pk})


class AutoriaEditView(GenericView):
    template_name = "materia/autoria_edit.html"

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        autorias = Autoria.objects.filter(materia=materia)
        autor = Autor.objects.get(id=self.kwargs['id'])
        form = AutoriaForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'autorias': autorias,
             'tipo_autores': TipoAutor.objects.all(),
             'autores': Autor.objects.all(),
             'tipo_autor_id': autor.tipo.id,
             'autor_id': autor.id})

    def post(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        autorias = Autoria.objects.filter(materia=materia)
        form = AutoriaForm(request.POST)

        if 'salvar' in request.POST:
            if int(form.data['primeiro_autor']) == 1:
                primeiro = True
            else:
                primeiro = False

            autor = Autor.objects.get(
                id=int(form.data['nome_autor']))

            try:
                autoria = Autoria.objects.get(
                    autor=autor,
                    materia=materia
                )
            except ObjectDoesNotExist:

                autoria = Autoria()
                autoria.autor = autor
                autoria.materia = materia
                autoria.primeiro_autor = primeiro
                autoria.save()

                return self.render_to_response(
                    {'object': materia,
                     'form': form,
                     'autorias': autorias,
                     'tipo_autores': TipoAutor.objects.all(),
                     'autores': Autor.objects.all(),
                     'tipo_autor_id': int(form.data['tipo_autor'])})
            else:
                msg = 'Essa autoria já foi adicionada!'
                messages.add_message(request, messages.INFO, msg)
                return self.render_to_response(
                    {'object': materia,
                     'form': form,
                     'autorias': autorias,
                     'tipo_autores': TipoAutor.objects.all(),
                     'autores': Autor.objects.all(),
                     'tipo_autor_id': int(form.data['tipo_autor'])})
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'autorias': autorias,
                 'tipo_autores': TipoAutor.objects.all(),
                 'autores': Autor.objects.all(),
                 'tipo_autor_id': int(form.data['tipo_autor'])})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('autoria', kwargs={'pk': pk})


class ProposicaoForm(ModelForm):

    descricao = forms.CharField(
        label='Descrição', required=True,
        widget=forms.Textarea())

    tipo_materia = forms.ModelChoiceField(
        label='Matéria Vinculada',
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número', required=False)

    ano_materia = forms.CharField(
        label='Ano', required=False)

    class Meta:
        model = Proposicao
        fields = ['tipo',
                  'descricao',
                  'texto_original']
        exclude = ['autor',
                   'data_envio',
                   'data_recebimento',
                   'data_devolucao',
                   'justificativa_devolucao',
                   'numero_proposicao',
                   'status',
                   'materia',
                   'documento']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo', 12)])
        row2 = sapl.layout.to_row(
            [('descricao', 12)])
        row3 = sapl.layout.to_row(
            [('tipo_materia', 4),
             ('numero_materia', 4),
             ('ano_materia', 4)])
        row4 = sapl.layout.to_row(
            [('texto_original', 10)])

        row4.append(
            Column(form_actions(), css_class='col-md-2'))

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Incluir Proposição',
                     row1, row2, row3, row4)
        )
        super(ProposicaoForm, self).__init__(
            *args, **kwargs)


class ProposicaoView(FormMixin, GenericView):
    template_name = "materia/proposicao.html"

    def get_success_url(self):
        return reverse('list_proposicao')

    def get(self, request, *args, **kwargs):
        form = ProposicaoForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = ProposicaoForm(request.POST)

        if form.is_valid():
            proposicao = form.save(commit=False)
            if 'texto_original' in request.FILES:
                proposicao.texto_original = request.FILES['texto_original']

            tipo = TipoProposicao.objects.get(
                id=int(request.POST['tipo']))

            if tipo.descricao == 'Parecer':
                try:
                    materia = MateriaLegislativa.objects.get(
                        tipo_id=int(form.data['tipo_materia']),
                        ano=int(form.data['ano_materia']),
                        numero=int(form.data['numero_materia']))
                except ObjectDoesNotExist:
                    msg = 'Matéria adicionada não existe!'
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response({'form': form})
                else:
                    proposicao.autor = materia.autoria_set.first().autor
                    proposicao.materia = materia

            proposicao.descricao = sub('&nbsp;',
                                       ' ',
                                       strip_tags(form.data['descricao']))
            # proposicao.data_envio = datetime.now()
            proposicao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form})


class ProposicaoListView(ListView):
    template_name = "materia/proposicao_list.html"
    paginate_by = 10
    model = Proposicao

    def get_queryset(self):
        return Proposicao.objects.all().order_by('-data_envio')

    def get_context_data(self, **kwargs):
        context = super(ProposicaoListView, self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = sapl.crud.make_pagination(
            page_obj.number, paginator.num_pages)
        return context


def em_tramitacao():
    return [('', 'Tanto Faz'),
            (True, 'Sim'),
            (False, 'Não')]


class MateriaLegislativaPesquisaForm(forms.Form):
    autor = forms.ModelChoiceField(
        label='Autor',
        required=False,
        queryset=Autor.objects.all().order_by('tipo'),
        empty_label='Selecione',
    )

    # relatores são os parlamentares ativos?
    relator = forms.ModelChoiceField(
        label='Relator',
        required=False,
        queryset=Parlamentar.objects.all().order_by('nome_parlamentar'),
        empty_label='Selecione',
    )

    tipo = forms.ModelChoiceField(
        label='Tipo de Matéria',
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    data_apresentacao = forms.DateField(label=u'Data de Apresentação',
                                        input_formats=['%d/%m/%Y'],
                                        required=False,
                                        widget=forms.DateInput(
                                            format='%d/%m/%Y',
                                            attrs={'class': 'dateinput'}))

    data_publicacao = forms.DateField(label=u'Data da Publicação',
                                      input_formats=['%d/%m/%Y'],
                                      required=False,
                                      widget=forms.DateInput(
                                          format='%d/%m/%Y',
                                          attrs={'class': 'dateinput'}))

    numero = forms.CharField(required=False, label=u'Número da Matéria')
    numero_protocolo = forms.CharField(required=False, label=u'Núm. Protocolo')
    ano = forms.CharField(required=False, label=u'Ano da Matéria')
    assunto = forms.CharField(required=False, label=u'Assunto')

    localizacao = forms.ModelChoiceField(
        label='Localização Atual',
        required=False,
        queryset=UnidadeTramitacao.objects.all(),
        empty_label='Selecione',
    )

    situacao = forms.ModelChoiceField(
        label='Situação',
        required=False,
        queryset=StatusTramitacao.objects.all(),
        empty_label='Selecione',
    )

    tramitacao = forms.ChoiceField(required=False,
                                   label='Tramitando',
                                   choices=em_tramitacao(),
                                   widget=forms.Select(
                                       attrs={'class': 'selector'}))

    # TODO: Verificar se esses campos estão corretos
    # assunto? # -> usado 'ementa' em 'assunto'
    # localizacao atual? #
    # situacao? #
    # tramitando? #

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo', 12)])
        row2 = sapl.layout.to_row(
            [('numero', 4),
             ('ano', 4),
             ('numero_protocolo', 4)])
        row3 = sapl.layout.to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row4 = sapl.layout.to_row(
            [('autor', 6),
             ('relator', 6)])
        row5 = sapl.layout.to_row(
            [('localizacao', 6),
             ('situacao', 6)])
        row6 = sapl.layout.to_row(
            [('tramitacao', 12)])
        row7 = sapl.layout.to_row(
            [('assunto', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Pesquisa Básica',
                     row1, row2, row3, row4, row5, row6, row7),
            form_actions(save_label='Pesquisar')
        )
        super(MateriaLegislativaPesquisaForm, self).__init__(
            *args, **kwargs)


class MateriaLegislativaPesquisaView(FormMixin, GenericView):
    template_name = 'materia/pesquisa_materia.html'

    def get_success_url(self):
        return reverse('pesquisar_materia')

    def get(self, request, *args, **kwargs):
        form = MateriaLegislativaPesquisaForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        kwargs = {}
        form = MateriaLegislativaPesquisaForm()
        # TODO: Autor, Relator, Localização, Origem

        if request.POST['tipo']:
            kwargs['tipo'] = request.POST['tipo']

        if request.POST['numero']:
            try:
                int(request.POST['numero'])
            except ValueError:
                mensagem = "Insira um número inteiro em matéria!"
                messages.add_message(request, messages.INFO, mensagem)
                return self.render_to_response(
                    {'form': form})
            else:
                kwargs['numero'] = request.POST['numero']

        if request.POST['ano']:
            try:
                int(request.POST['ano'])
            except ValueError:
                mensagem = "Insira uma data válida em Ano da Matéria!"
                messages.add_message(request, messages.INFO, mensagem)
                return self.render_to_response(
                    {'form': form})
            else:
                kwargs['ano'] = request.POST['ano']

        if request.POST['numero_protocolo']:
            try:
                int(request.POST['numero_protocolo'])
            except ValueError:
                mensagem = "Insira um Número de Protocolo válido!"
                messages.add_message(request, messages.INFO, mensagem)
                return self.render_to_response(
                    {'form': form})
            else:
                kwargs['numero_protocolo'] = request.POST['numero_protocolo']

        if request.POST['data_apresentacao']:
            try:
                datetime.strptime(
                    request.POST['data_apresentacao'],
                    '%d/%m/%Y').strftime('%Y-%m-%d')
            except ValueError:
                mensagem = "Insira uma Data de Apresentação válida!"
                messages.add_message(request, messages.INFO, mensagem)
                return self.render_to_response(
                    {'form': form})
            else:
                kwargs['data_apresentacao'] = datetime.strptime(
                    request.POST['data_apresentacao'],
                    '%d/%m/%Y').strftime('%Y-%m-%d')

        if request.POST['data_publicacao']:
            try:
                datetime.strptime(
                    request.POST['data_publicacao'],
                    '%d/%m/%Y').strftime('%Y-%m-%d')
            except ValueError:
                mensagem = "Insira uma Data de Publicação válida!"
                messages.add_message(request, messages.INFO, mensagem)
                return self.render_to_response(
                    {'form': form})
            else:
                kwargs['data_publicacao'] = datetime.strptime(
                    request.POST['data_publicacao'],
                    '%d/%m/%Y').strftime('%Y-%m-%d')

        if request.POST['tramitacao']:
            kwargs['em_tramitacao'] = request.POST['tramitacao']

        if request.POST['assunto']:
            kwargs['ementa'] = request.POST['assunto']

        if request.POST['autor']:
            kwargs['autoria__autor__id'] = request.POST['autor']

        if request.POST['relator']:
            kwargs['relatoria__parlamentar__id'] = request.POST['relator']

        if request.POST['localizacao']:
            local = request.POST['localizacao']
            kwargs['tramitacao__unidade_tramitacao_destino'] = local

        if request.POST['situacao']:
            kwargs['tramitacao__status'] = request.POST['situacao']

        request.session['kwargs'] = kwargs
        return redirect('pesquisar_materia_list')


class PesquisaMateriaListView(FormMixin, ListView):
    template_name = 'materia/pesquisa_materia_list.html'
    context_object_name = 'materias'
    model = MateriaLegislativa
    paginate_by = 10

    def get_queryset(self):
        # import ipdb; ipdb.set_trace()

        kwargs = self.request.session['kwargs']
        lista_materias = MateriaLegislativa.objects.filter(**kwargs)
        materias = []

        if (kwargs.get('tramitacao__unidade_tramitacao_destino') and
                kwargs.get('tramitacao__status')):
            local = int(kwargs['tramitacao__unidade_tramitacao_destino'])
            status = int(kwargs['tramitacao__status'])
            for m in lista_materias:
                l = m.tramitacao_set.last().unidade_tramitacao_destino_id
                s = m.tramitacao_set.last().status_id
                if l == local and s == status:
                    materias.append(m)
            return materias

        if kwargs.get('tramitacao__unidade_tramitacao_destino'):
            local = int(kwargs['tramitacao__unidade_tramitacao_destino'])
            for m in lista_materias:
                l = m.tramitacao_set.last().unidade_tramitacao_destino_id
                if l == local:
                    materias.append(m)
            return materias

        if kwargs.get('tramitacao__status'):
            status = int(kwargs['tramitacao__status'])
            for m in lista_materias:
                s = m.tramitacao_set.last().status_id
                if s == status:
                    materias.append(m)
            return materias

        else:
            return lista_materias

        # kwargs = self.request.session['kwargs']
        # id_parlamentar = kwargs.get('relatoria')
        # if kwargs.get('relatoria'):
        #     kwargs.pop('relatoria')
        #     materias = MateriaLegislativa.objects.filter(**kwargs)
        #     if not kwargs.get('autoria'):
        #         return MateriaLegislativa.objects.filter(
        #             relatoria__parlamentar__id=id_parlamentar,
        #             relatoria__data_destituicao_relator__isnull=True,
        #             relatoria__materia__in=materias)
        #     else:
        #         id_parlamentar_autoria = kwargs.get('autoria')
        #         kwargs.pop('autoria')
        #         materias = MateriaLegislativa.objects.filter(**kwargs)
        #         return MateriaLegislativa.objects.filter(
        #             relatoria__parlamentar__id=id_parlamentar,
        #             relatoria__data_destituicao_relator__isnull=True,
        #             autoria__autor__id=id_parlamentar_autoria,
        #             autoria__materia__in=materias,
        #             relatoria__materia__in=materias)

        # if kwargs.get('autoria'):
        #     id_parlamentar = kwargs.get('autoria')
        #     kwargs.pop('autoria')
        #     materias = MateriaLegislativa.objects.filter(**kwargs)
        #     return MateriaLegislativa.objects.filter(
        #             autoria__autor__id=id_parlamentar,
        #             autoria__materia__in=materias)

    def get_context_data(self, **kwargs):
        context = super(PesquisaMateriaListView, self).get_context_data(
            **kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = sapl.crud.make_pagination(
            page_obj.number, paginator.num_pages)
        return context


class MateriaTaView(IntegracaoTaView):
    model = MateriaLegislativa


class ProposicaoTaView(IntegracaoTaView):
    model = Proposicao
