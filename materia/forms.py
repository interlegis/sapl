from datetime import date

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Fieldset, Layout
from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from norma.models import LegislacaoCitada, TipoNormaJuridica
from parlamentares.models import Parlamentar, Partido

from .models import (AcompanhamentoMateria, Anexada, Autor, DespachoInicial,
                     DocumentoAcessorio, MateriaLegislativa, Numeracao, Origem,
                     Proposicao, Relatoria, StatusTramitacao, TipoAutor,
                     TipoDocumento, TipoMateriaLegislativa, Tramitacao,
                     UnidadeTramitacao)


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


def em_tramitacao():
    return [('', 'Tanto Faz'),
            (True, 'Sim'),
            (False, 'Não')]


def ordenacao_materias():
    return [(1, 'Crescente'),
            (2, 'Decrescente')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


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

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 12)])
        row2 = crispy_layout_mixin.to_row(
            [('descricao', 12)])
        row3 = crispy_layout_mixin.to_row(
            [('tipo_materia', 4),
             ('numero_materia', 4),
             ('ano_materia', 4)])
        row4 = crispy_layout_mixin.to_row(
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


class AcompanhamentoMateriaForm(ModelForm):

    class Meta:
        model = AcompanhamentoMateria
        fields = ['email']

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row([('email', 10)])

        row1.append(
            Column(form_actions(save_label='Cadastrar'), css_class='col-md-2')
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Acompanhamento de Matéria por e-mail', row1
            )
        )
        super(AcompanhamentoMateriaForm, self).__init__(*args, **kwargs)


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

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4),
             ('nome', 4),
             ('data', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('autor', 12)])

        row3 = crispy_layout_mixin.to_row(
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
        row1 = crispy_layout_mixin.to_row(
            [('data_tramitacao', 6),
             ('unidade_tramitacao_local', 6)])

        row2 = crispy_layout_mixin.to_row(
            [('status', 5),
             ('turno', 5),
             ('urgente', 2)])

        row3 = crispy_layout_mixin.to_row(
            [('unidade_tramitacao_destino', 12)])

        row4 = crispy_layout_mixin.to_row(
            [('data_encaminhamento', 6),
             ('data_fim_prazo', 6)])

        row5 = crispy_layout_mixin.to_row(
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

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('disposicao', 3),
             ('parte', 3),
             ('livro', 3),
             ('titulo', 3)])

        row3 = crispy_layout_mixin.to_row(
            [('capitulo', 3),
             ('secao', 3),
             ('subsecao', 3),
             ('artigo', 3)])

        row4 = crispy_layout_mixin.to_row(
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

        row1 = crispy_layout_mixin.to_row(
            [('tipo_materia', 12)])
        row2 = crispy_layout_mixin.to_row(
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


class DespachoInicialForm(ModelForm):

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
        super(DespachoInicialForm, self).__init__(*args, **kwargs)


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

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])
        row2 = crispy_layout_mixin.to_row(
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

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('data_apresentacao', 4),
             ('numero_protocolo', 4),
             ('regime_tramitacao', 4)])

        row3 = crispy_layout_mixin.to_row(
            [('texto_original', 9),
             ('em_tramitacao', 3)])

        row4 = crispy_layout_mixin.to_row(
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


class AutoriaForm(forms.Form):
    tipo_autor = forms.CharField()
    nome_autor = forms.CharField()
    primeiro_autor = forms.CharField()
    partido_autor = forms.ModelChoiceField(
        label='Partido (Autor)',
        required=False,
        queryset=Partido.objects.all(),
        empty_label='Selecione')


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

    ordem = forms.ChoiceField(required=False,
                              label='Ordenação',
                              choices=ordenacao_materias(),
                              widget=forms.Select(
                                       attrs={'class': 'selector'}))

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

    tipo_autor = forms.ModelChoiceField(
        label='Tipo Autor',
        required=False,
        queryset=TipoAutor.objects.all(),
        empty_label='Selecione',
    )

    partido_autor = forms.ModelChoiceField(
        label='Partido (Autor)',
        required=False,
        queryset=Partido.objects.all(),
        empty_label='Selecione')

    local_origem_externa = forms.ModelChoiceField(
        label='Localização de Origem',
        required=False,
        queryset=Origem.objects.all(),
        empty_label='Selecione')

    # TODO: Verificar se esses campos estão corretos
    # assunto? # -> usado 'ementa' em 'assunto'
    # localizacao atual? #
    # situacao? #
    # tramitando? #

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 12)])
        row2 = crispy_layout_mixin.to_row(
            [('numero', 4),
             ('ano', 4),
             ('numero_protocolo', 4)])
        row3 = crispy_layout_mixin.to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row4 = crispy_layout_mixin.to_row(
            [('autor', 6),
             ('partido_autor', 6)])
        row5 = crispy_layout_mixin.to_row(
            [('tipo_autor', 6),
             ('relator', 6)])
        row6 = crispy_layout_mixin.to_row(
            [('local_origem_externa', 6),
             ('localizacao', 6)])
        row7 = crispy_layout_mixin.to_row(
            [('tramitacao', 4),
             ('situacao', 4),
             ('ordem', 4)])
        row8 = crispy_layout_mixin.to_row(
            [('assunto', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Pesquisa Básica',
                     row1, row2, row3, row4, row5, row6, row7, row8),
            form_actions(save_label='Pesquisar')
        )
        super(MateriaLegislativaPesquisaForm, self).__init__(
            *args, **kwargs)
