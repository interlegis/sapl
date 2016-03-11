from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Fieldset, Layout, Submit
from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from norma.models import LegislacaoCitada, TipoNormaJuridica
from parlamentares.models import Parlamentar, Partido

from .models import (AcompanhamentoMateria, Anexada, Autor, Autoria,
                     DespachoInicial, DocumentoAcessorio, MateriaLegislativa,
                     Numeracao, Origem, Proposicao, Relatoria,
                     StatusTramitacao, TipoAutor, TipoMateriaLegislativa,
                     Tramitacao, UnidadeTramitacao)

EM_TRAMITACAO = [('', _('Tanto Faz')),
                 (True, 'Sim'),
                 (False, 'Não')]

ORDENACAO_MATERIAIS = [(1, 'Crescente'),
                       (2, 'Decrescente')]


class ProposicaoForm(ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label=_('Matéria Vinculada'),
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
            Fieldset(_('Incluir Proposição'),
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
                _('Acompanhamento de Matéria por e-mail'), row1
            )
        )
        super(AcompanhamentoMateriaForm, self).__init__(*args, **kwargs)


class DocumentoAcessorioForm(ModelForm):

    class Meta:
        model = DocumentoAcessorio
        fields = ['tipo',
                  'nome',
                  'data',
                  'autor',
                  'ementa']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'dateinput'})
        }

    def __init__(self, excluir=False, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4), ('nome', 4), ('data', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('autor', 12)])

        row3 = crispy_layout_mixin.to_row(
            [('ementa', 12)])

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Incluir Documento Acessório'),
                row1, row2, row3,
                form_actions(more=more)
            )
        )
        super(DocumentoAcessorioForm, self).__init__(*args, **kwargs)


class RelatoriaForm(ModelForm):

    class Meta:
        model = Relatoria
        fields = ['data_designacao_relator',
                  'comissao',
                  'parlamentar',
                  'data_destituicao_relator',
                  'tipo_fim_relatoria'
                  ]
        widgets = {
            'data_designacao_relator': forms.DateInput(attrs={
                'class': 'dateinput'}),
            'data_destituicao_relator': forms.DateInput(attrs={
                                                        'class': 'dateinput'}),
        }


class TramitacaoForm(ModelForm):

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

    def __init__(self, excluir=False, *args, **kwargs):
        row1 = crispy_layout_mixin.to_row(
            [('data_tramitacao', 6), ('unidade_tramitacao_local', 6)])

        row2 = crispy_layout_mixin.to_row(
            [('status', 5), ('turno', 5), ('urgente', 2)])

        row3 = crispy_layout_mixin.to_row(
            [('unidade_tramitacao_destino', 12)])

        row4 = crispy_layout_mixin.to_row(
            [('data_encaminhamento', 6), ('data_fim_prazo', 6)])

        row5 = crispy_layout_mixin.to_row(
            [('texto', 12)])

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Incluir Tramitação'),
                     row1, row2, row3, row4, row5,
                     ),
            form_actions(more=more)
        )
        super(TramitacaoForm, self).__init__(
            *args, **kwargs)


class LegislacaoCitadaForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label=_('Tipo Norma'),
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
                _('Incluir Legislação Citada'),
                row1, row2, row3, row4,
                form_actions()
            )
        )
        super(LegislacaoCitadaForm, self).__init__(*args, **kwargs)


class NumeracaoForm(ModelForm):

    class Meta:
        model = Numeracao
        fields = ['tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'data_materia']

    def __init__(self, excluir=False, *args, **kwargs):
        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]

        row1 = crispy_layout_mixin.to_row(
            [('tipo_materia', 12)])
        row2 = crispy_layout_mixin.to_row(
            [('numero_materia', 4), ('ano_materia', 4), ('data_materia', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Incluir Numeração'),
                row1, row2,
                form_actions(more=more)
            )
        )
        super(NumeracaoForm, self).__init__(*args, **kwargs)


class DespachoInicialForm(ModelForm):

    class Meta:
        model = DespachoInicial
        fields = ['comissao']

    def __init__(self, excluir=False, *args, **kwargs):

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Adicionar Despacho Inicial'),
                'comissao',
                form_actions(more=more)
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

    class Meta:
        model = Anexada
        fields = ['tipo', 'numero', 'ano',
                  'data_anexacao', 'data_desanexacao']
        widgets = {
            'data_anexacao': forms.DateInput(attrs={'class': 'dateinput'}),
            'data_desanexacao': forms.DateInput(attrs={'class': 'dateinput'}),
        }

    def __init__(self, excluir=False, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4), ('numero', 4), ('ano', 4)])
        row2 = crispy_layout_mixin.to_row(
            [('data_anexacao', 6), ('data_desanexacao', 6)])

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Anexar Matéria'),
                row1, row2,
                form_actions(more=more)
            )
        )
        super(MateriaAnexadaForm, self).__init__(
            *args, **kwargs)


class FormularioSimplificadoForm(ModelForm):

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
        exclude = ['anexadas']
        widgets = {
            'data_apresentacao': forms.DateInput(attrs={'class': 'dateinput'}),
        }

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
                _('Formulário Simplificado'),
                Fieldset(
                    _('Identificação Básica'),
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
                _('Formulário de Cadastro'),
                Fieldset(
                    _('Identificação Básica'),
                    'tipo',
                    'numero',
                    'ano',
                    'data_apresentacao',
                    'numero_protocolo',
                    'tipo_apresentacao',
                    'texto_original'
                ),
                Fieldset(
                    _('Outras Informações'),
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
                    _('Origem Externa'),
                    'tipo_origem_externa',
                    'numero_origem_externa',
                    'ano_origem_externa',
                    'local_origem_externa',
                    'data_origem_externa'
                ),
                Fieldset(
                    _('Dados Textuais'),
                    'ementa',
                    'indexacao',
                    'observacao'
                ),
                form_actions()
            )
        )
        super(FormularioCadastroForm, self).__init__(*args, **kwargs)


class AutoriaForm(ModelForm):
    autor = forms.ModelChoiceField(
        label=_('Autor'),
        required=True,
        queryset=Autor.objects.all().order_by('tipo', 'nome'),
    )
    primeiro_autor = forms.ChoiceField(
        label=_('Primeiro Autor'),
        required=True,
        choices=[(True, _('Sim')), (False, _('Não'))],
    )

    class Meta:
        model = Autoria
        fields = ['autor',
                  'primeiro_autor',
                  'partido']

    def __init__(self, excluir=False, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('autor', 4), ('primeiro_autor', 4), ('partido', 4)])

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Adicionar Autoria'),
                row1,
                form_actions(more=more)
            )
        )
        super(AutoriaForm, self).__init__(
            *args, **kwargs)


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
        label=_('Tipo de Matéria'),
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
                              choices=ORDENACAO_MATERIAIS,
                              widget=forms.Select(
                                    attrs={'class': 'selector'}))

    localizacao = forms.ModelChoiceField(
        label=_('Localização Atual'),
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
                                   choices=EM_TRAMITACAO,
                                   widget=forms.Select(
                                       attrs={'class': 'selector'}))

    tipo_autor = forms.ModelChoiceField(
        label=_('Tipo Autor'),
        required=False,
        queryset=TipoAutor.objects.all(),
        empty_label='Selecione',
    )

    partido_autor = forms.ModelChoiceField(
        label=_('Partido (Autor)'),
        required=False,
        queryset=Partido.objects.all(),
        empty_label='Selecione')

    local_origem_externa = forms.ModelChoiceField(
        label=_('Localização de Origem'),
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
            Fieldset(_('Pesquisa Básica'),
                     row1, row2, row3, row4, row5, row6, row7, row8),
            form_actions(save_label='Pesquisar')
        )
        super(MateriaLegislativaPesquisaForm, self).__init__(
            *args, **kwargs)
