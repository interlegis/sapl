import django_filters
from crispy_forms.bootstrap import (FormActions)
from crispy_forms.layout import (HTML, Button, Fieldset,
                                 Layout, Submit)
from django import forms
from django.utils.translation import ugettext_lazy as _

from sapl.audiencia.models import AudienciaPublica
from sapl.base.models import Autor
from sapl.comissoes.models import Reuniao
from sapl.crispy_layout_mixin import SaplFormHelper, to_row, form_actions
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa, MateriaEmTramitacao, UnidadeTramitacao, \
    StatusTramitacao
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria
from sapl.utils import FilterOverridesMetaMixin, choice_anos_com_normas, qs_override_django_filter, \
    choice_anos_com_materias, choice_tipos_normas, autor_label, autor_modal


class RelatorioDocumentosAcessoriosFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioDocumentosAcessoriosFilterSet, self).qs
        return parent.distinct().order_by('-data')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAcessorio
        fields = ['tipo', 'materia__tipo', 'data']

    def __init__(self, *args, **kwargs):
        super(
            RelatorioDocumentosAcessoriosFilterSet, self
        ).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['materia__tipo'].label = 'Tipo de Matéria do Documento'
        self.filters['data'].label = 'Período (Data Inicial - Data Final)'

        self.form.fields['tipo'].required = True

        row0 = to_row([('tipo', 6),
                       ('materia__tipo', 6)])

        row1 = to_row([('data', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                                   <div class="form-check">
                                                       <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                       <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                   </div>
                                               ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa'),
                     row0, row1,
                     buttons)
        )


class RelatorioAtasFilterSet(django_filters.FilterSet):
    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ['data_inicio']

    @property
    def qs(self):
        parent = super(RelatorioAtasFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').exclude(
            upload_ata='').order_by('-data_inicio', 'tipo', 'numero')

    def __init__(self, *args, **kwargs):
        super(RelatorioAtasFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['data_inicio'].label = 'Período de Abertura (Inicial - Final)'
        self.form.fields['data_inicio'].required = False

        row1 = to_row([('data_inicio', 12)])

        buttons = FormActions(
            *[
                HTML('''
                        <div class="form-check">
                            <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                            <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                        </div>
                    ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Atas das Sessões Plenárias'),
                     row1, buttons, )
        )


def ultimo_ano_com_norma():
    anos_normas = choice_anos_com_normas()

    if anos_normas:
        return anos_normas[0]
    return ''


class RelatorioNormasMesFilterSet(django_filters.FilterSet):
    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Norma',
                                      choices=choice_anos_com_normas,
                                      initial=ultimo_ano_com_norma)

    tipo = django_filters.ChoiceFilter(required=False,
                                       label='Tipo Norma',
                                       choices=choice_tipos_normas,
                                       initial=0)

    class Meta:
        model = NormaJuridica
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioNormasMesFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['ano'].label = 'Ano'
        self.form.fields['ano'].required = True

        row1 = to_row([('ano', 6), ('tipo', 6)])

        buttons = FormActions(
            *[
                HTML('''
                            <div class="form-check col-auto">
                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                            </div>
                    ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por mês do ano.'),
                     row1, buttons, )
        )

    @property
    def qs(self):
        parent = super(RelatorioNormasMesFilterSet, self).qs
        return parent.distinct().order_by('data')


class RelatorioPresencaSessaoFilterSet(django_filters.FilterSet):
    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ['data_inicio',
                  'sessao_legislativa',
                  'tipo',
                  'legislatura']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.form.fields['exibir_ordem_dia'] = forms.BooleanField(
            required=False, label='Exibir presença das Ordens do Dia')
        self.form.initial['exibir_ordem_dia'] = True

        self.form.fields['exibir_somente_titular'] = forms.BooleanField(
            required=False, label='Exibir somente parlamentares titulares')
        self.form.initial['exibir_somente_titular'] = False

        self.form.fields['exibir_somente_ativo'] = forms.BooleanField(
            required=False, label='Exibir somente parlamentares ativos')
        self.form.initial['exibir_somente_ativo'] = False

        self.form.fields['legislatura'].required = True

        self.filters['data_inicio'].label = 'Período (Inicial - Final)'

        tipo_sessao_ordinaria = self.filters['tipo'].queryset.filter(
            nome='Ordinária')
        if tipo_sessao_ordinaria:
            self.form.initial['tipo'] = tipo_sessao_ordinaria.first()

        row1 = to_row([('legislatura', 4),
                       ('sessao_legislativa', 4),
                       ('tipo', 4)])
        row2 = to_row([('exibir_ordem_dia', 12),
                       ('exibir_somente_titular', 12),
                       ('exibir_somente_ativo', 12)])
        row3 = to_row([('data_inicio', 12)])

        buttons = FormActions(
            *[
                HTML('''
                        <div class="form-check">
                            <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                            <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                        </div>
                    ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Presença dos parlamentares nas sessões plenárias'),
                     row1, row2, row3, buttons, )
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


class RelatorioHistoricoTramitacaoFilterSet(django_filters.FilterSet):
    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super(RelatorioHistoricoTramitacaoFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'tramitacao__status', 'tramitacao__data_tramitacao',
                  'tramitacao__unidade_tramitacao_local', 'tramitacao__unidade_tramitacao_destino']

    def __init__(self, *args, **kwargs):
        super(RelatorioHistoricoTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['tramitacao__status'].label = _('Status')
        self.filters['tramitacao__unidade_tramitacao_local'].label = _(
            'Unidade Local (Origem)')
        self.filters['tramitacao__unidade_tramitacao_destino'].label = _(
            'Unidade Destino')

        row1 = to_row([('tramitacao__data_tramitacao', 12)])
        row2 = to_row([('tramitacao__unidade_tramitacao_local', 6),
                       ('tramitacao__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacao__status', 6)])

        row4 = to_row([
            ('autoria__autor', 0),
            (Button('pesquisar',
                    'Pesquisar Autor',
                    css_class='btn btn-primary btn-sm'), 2),
            (Button('limpar',
                    'Limpar Autor',
                    css_class='btn btn-primary btn-sm'), 2)
        ])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2, row3, row4,
                     HTML(autor_label),
                     HTML(autor_modal),
                     buttons, )
        )


class RelatorioDataFimPrazoTramitacaoFilterSet(django_filters.FilterSet):
    materia__ano = django_filters.ChoiceFilter(required=False,
                                               label='Ano da Matéria',
                                               choices=choice_anos_com_materias)

    @property
    def qs(self):
        parent = super(RelatorioDataFimPrazoTramitacaoFilterSet, self).qs
        return parent.distinct().prefetch_related('materia__tipo').order_by('tramitacao__data_fim_prazo', 'materia__tipo', 'materia__numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaEmTramitacao
        fields = ['materia__tipo',
                  'tramitacao__unidade_tramitacao_local',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status',
                  'tramitacao__data_fim_prazo']

    def __init__(self, *args, **kwargs):
        super(RelatorioDataFimPrazoTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['materia__tipo'].label = 'Tipo de Matéria'
        self.filters[
            'tramitacao__unidade_tramitacao_local'].label = 'Unidade Local (Origem)'
        self.filters['tramitacao__unidade_tramitacao_destino'].label = 'Unidade Destino'
        self.filters['tramitacao__status'].label = 'Status de tramitação'

        row1 = to_row([('materia__ano', 12)])
        row2 = to_row([('tramitacao__data_fim_prazo', 12)])
        row3 = to_row([('tramitacao__unidade_tramitacao_local', 6),
                       ('tramitacao__unidade_tramitacao_destino', 6)])
        row4 = to_row(
            [('materia__tipo', 6),
             ('tramitacao__status', 6)])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Tramitações'),
                     row1, row2, row3, row4,
                     buttons, )
        )


class RelatorioReuniaoFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioReuniaoFilterSet, self).qs
        return parent.distinct().order_by('-data', 'comissao')

    class Meta:
        model = Reuniao
        fields = ['comissao', 'data',
                  'nome', 'tema']

    def __init__(self, *args, **kwargs):
        super(RelatorioReuniaoFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row([('data', 12)])
        row2 = to_row(
            [('comissao', 4),
             ('nome', 4),
             ('tema', 4)])

        buttons = FormActions(
            *[
                HTML('''
                                                                    <div class="form-check">
                                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                                    </div>
                                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Reunião de Comissão'),
                     row1, row2,
                     buttons, )
        )


class RelatorioAudienciaFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioAudienciaFilterSet, self).qs
        return parent.distinct().order_by('-data', 'tipo')

    class Meta:
        model = AudienciaPublica
        fields = ['tipo', 'data',
                  'nome']

    def __init__(self, *args, **kwargs):
        super(RelatorioAudienciaFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row([('data', 12)])
        row2 = to_row(
            [('tipo', 4),
             ('nome', 4)])

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Audiência Pública'),
                     row1, row2,
                     buttons, )
        )


class RelatorioMateriasTramitacaoFilterSet(django_filters.FilterSet):
    materia__ano = django_filters.ChoiceFilter(required=True,
                                               label='Ano da Matéria',
                                               choices=choice_anos_com_materias)

    tramitacao__unidade_tramitacao_destino = django_filters.ModelChoiceFilter(
        queryset=UnidadeTramitacao.objects.all(),
        label=_('Unidade Atual'))

    tramitacao__status = django_filters.ModelChoiceFilter(
        queryset=StatusTramitacao.objects.all(),
        label=_('Status Atual'))

    materia__autores = django_filters.ModelChoiceFilter(
        label='Autor da Matéria',
        queryset=Autor.objects.all())

    @property
    def qs(self):
        parent = super(RelatorioMateriasTramitacaoFilterSet, self).qs
        return parent.distinct().order_by(
            '-materia__ano', 'materia__tipo', '-materia__numero'
        )

    class Meta:
        model = MateriaEmTramitacao
        fields = ['materia__ano', 'materia__tipo',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status', 'materia__autores']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['materia__tipo'].label = 'Tipo de Matéria'

        row1 = to_row([('materia__ano', 12)])
        row2 = to_row([('materia__tipo', 12)])
        row3 = to_row([('tramitacao__unidade_tramitacao_destino', 12)])
        row4 = to_row([('tramitacao__status', 12)])
        row5 = to_row([('materia__autores', 12)])

        buttons = FormActions(
            *[
                HTML('''
                            <div class="form-check">
                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                            </div>
                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria em Tramitação'),
                     row1, row2, row3, row4, row5,
                     buttons, )
        )


class RelatorioMateriasPorAnoAutorTipoFilterSet(django_filters.FilterSet):
    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Matéria',
                                      choices=choice_anos_com_materias)

    class Meta:
        model = MateriaLegislativa
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasPorAnoAutorTipoFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row(
            [('ano', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                    <div class="form-check">
                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                    </div>
                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria por Ano Autor Tipo'),
                     row1,
                     buttons, )
        )


class RelatorioMateriasPorAutorFilterSet(django_filters.FilterSet):
    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct().order_by('-ano', '-numero', 'tipo', 'autoria__autor', '-autoria__primeiro_autor')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('data_apresentacao', 12)])
        row3 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria por Autor'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     buttons, )
        )


class RelatorioHistoricoTramitacaoAdmFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioHistoricoTramitacaoAdmFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAdministrativo
        fields = ['tipo', 'tramitacaoadministrativo__status',
                  'tramitacaoadministrativo__data_tramitacao',
                  'tramitacaoadministrativo__unidade_tramitacao_local',
                  'tramitacaoadministrativo__unidade_tramitacao_destino']

    def __init__(self, *args, **kwargs):
        super(RelatorioHistoricoTramitacaoAdmFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['tramitacaoadministrativo__status'].label = _('Status')
        self.filters['tramitacaoadministrativo__unidade_tramitacao_local'].label = _(
            'Unidade Local (Origem)')
        self.filters['tramitacaoadministrativo__unidade_tramitacao_destino'].label = _(
            'Unidade Destino')

        row1 = to_row([('tramitacaoadministrativo__data_tramitacao', 12)])
        row2 = to_row([('tramitacaoadministrativo__unidade_tramitacao_local', 6),
                       ('tramitacaoadministrativo__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacaoadministrativo__status', 6)])

        buttons = FormActions(
            *[
                HTML('''
                                                            <div class="form-check">
                                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                            </div>
                                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_(''),
                     row1, row2, row3,
                     buttons, )
        )


class RelatorioNormasPorAutorFilterSet(django_filters.FilterSet):
    autorianorma__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct().filter(autorianorma__primeiro_autor=True) \
            .order_by('autorianorma__autor', '-autorianorma__primeiro_autor', 'tipo', '-ano', '-numero')

    class Meta(FilterOverridesMetaMixin):
        model = NormaJuridica
        fields = ['tipo', 'data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Norma'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('data', 12)])
        row3 = to_row(
            [('autorianorma__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        buttons = FormActions(
            *[
                HTML('''
                                                                    <div class="form-check">
                                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                                    </div>
                                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     form_actions(label='Pesquisar'))
        )


class RelatorioNormasVigenciaFilterSet(django_filters.FilterSet):
    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Norma',
                                      choices=choice_anos_com_normas,
                                      initial=ultimo_ano_com_norma)

    tipo = django_filters.ChoiceFilter(required=False,
                                       label='Tipo Norma',
                                       choices=choice_tipos_normas,
                                       initial=0)

    vigencia = forms.ChoiceField(
        label=_('Vigência'),
        choices=[(True, "Vigente"), (False, "Não vigente")],
        widget=forms.RadioSelect(),
        required=True,
        initial=True)

    def __init__(self, *args, **kwargs):
        super(RelatorioNormasVigenciaFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['ano'].label = 'Ano'
        self.form.fields['ano'].required = True
        self.form.fields['vigencia'] = self.vigencia

        row1 = to_row([('ano', 6), ('tipo', 6)])
        row2 = to_row([('vigencia', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por vigência.'),
                     row1, row2,
                     buttons, )
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)
