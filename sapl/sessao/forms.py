from datetime import datetime

import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Fieldset, Layout
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.materia.forms import MateriaLegislativaFilterSet
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.utils import (RANGE_DIAS_MES, RANGE_MESES,
                        MateriaPesquisaOrderingFilter, autor_label,
                        autor_modal)

from .models import (Bancada, ExpedienteMateria, Orador, OradorExpediente,
                     OrdemDia, SessaoPlenaria, SessaoPlenariaPresenca)


def recupera_anos():
    try:
        anos_list = SessaoPlenaria.objects.all().dates('data_inicio', 'year')
        # a listagem deve ser em ordem descrescente, mas por algum motivo
        # a adicao de .order_by acima depois do all() nao surte efeito
        # apos a adicao do .dates(), por isso o reversed() abaixo
        anos = [(k.year, k.year) for k in reversed(anos_list)]
        return anos
    except Exception:
        return []


def ANO_CHOICES():
    return [('', '---------')] + recupera_anos()


MES_CHOICES = [('', '---------')] + RANGE_MESES
DIA_CHOICES = [('', '---------')] + RANGE_DIAS_MES


ORDENACAO_RESUMO = [('cont_mult', 'Conteúdo Multimídia'),
                    ('exp', 'Expedientes'),
                    ('id_basica', 'Identificação Básica'),
                    ('lista_p', 'Lista de Presença'),
                    ('lista_p_o_d', 'Lista de Presença Ordem do Dia'),
                    ('mat_exp', 'Matérias do Expediente'),
                    ('mat_o_d', 'Matérias da Ordem do Dia'),
                    ('mesa_d', 'Mesa Diretora'),
                    ('oradores_exped', 'Oradores do Expediente'),
                    ('oradores_expli', 'Oradores das Explicações Pessoais')]


class BancadaForm(ModelForm):

    class Meta:
        model = Bancada
        fields = ['legislatura', 'nome', 'partido', 'data_criacao',
                  'data_extincao', 'descricao']

    def clean(self):
        super(BancadaForm, self).clean()

        if self.cleaned_data['data_extincao']:
            if (self.cleaned_data['data_extincao'] <
                    self.cleaned_data['data_criacao']):
                msg = _('Data de extinção não pode ser menor que a de criação')
                raise ValidationError(msg)
        return self.cleaned_data


class ExpedienteMateriaForm(ModelForm):

    _model = ExpedienteMateria

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número Matéria', required=True)

    ano_materia = forms.CharField(
        label='Ano Matéria', required=True)

    data_ordem = forms.CharField(
        label='Data Sessão',
        initial=datetime.now().strftime('%d/%m/%Y'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = ExpedienteMateria
        fields = ['data_ordem', 'numero_ordem', 'tipo_materia', 'observacao',
                  'numero_materia', 'ano_materia', 'tipo_votacao']

    def clean_numero_ordem(self):
        sessao = self.instance.sessao_plenaria

        numero_ordem_exists = ExpedienteMateria.objects.filter(
            sessao_plenaria=sessao,
            numero_ordem=self.cleaned_data['numero_ordem']).exists()

        if numero_ordem_exists and not self.instance.pk:
            msg = _('Esse número de ordem já existe.')
            raise ValidationError(msg)

        return self.cleaned_data['numero_ordem']

    def clean_data_ordem(self):
        return self.instance.sessao_plenaria.data_inicio

    def clean(self):
        super(ExpedienteMateriaForm, self).clean()

        cleaned_data = self.cleaned_data
        sessao = self.instance.sessao_plenaria

        try:
            materia = MateriaLegislativa.objects.get(
                numero=self.cleaned_data['numero_materia'],
                ano=self.cleaned_data['ano_materia'],
                tipo=self.cleaned_data['tipo_materia'])
        except ObjectDoesNotExist:
            msg = _('A matéria a ser inclusa não existe no cadastro'
                    ' de matérias legislativas.')
            raise ValidationError(msg)
        else:
            cleaned_data['materia'] = materia

        exists = self._model.objects.filter(
            sessao_plenaria=sessao,
            materia=materia).exists()

        if exists and not self.instance.pk:
            msg = _('Essa matéria já foi cadastrada.')
            raise ValidationError(msg)

        return cleaned_data

    def save(self, commit=False):
        expediente = super(ExpedienteMateriaForm, self).save(commit)
        expediente.materia = self.cleaned_data['materia']
        expediente.save()
        return expediente


class OrdemDiaForm(ExpedienteMateriaForm):

    _model = OrdemDia

    class Meta:
        model = OrdemDia
        fields = ['data_ordem', 'numero_ordem', 'tipo_materia', 'observacao',
                  'numero_materia', 'ano_materia', 'tipo_votacao']

    def clean_data_ordem(self):
        return self.instance.sessao_plenaria.data_inicio

    def clean_numero_ordem(self):
        sessao = self.instance.sessao_plenaria

        numero_ordem_exists = OrdemDia.objects.filter(
            sessao_plenaria=sessao,
            numero_ordem=self.cleaned_data['numero_ordem']).exists()

        if numero_ordem_exists and not self.instance.pk:
            msg = _('Esse número de ordem já existe.')
            raise ValidationError(msg)

        return self.cleaned_data['numero_ordem']

    def clean(self):
        super(OrdemDiaForm, self).clean()
        return self.cleaned_data

    def save(self, commit=False):
        ordem = super(OrdemDiaForm, self).save(commit)
        ordem.materia = self.cleaned_data['materia']
        ordem.save()
        return ordem


class PresencaForm(forms.Form):
    presenca = forms.CharField(required=False, initial=False)
    parlamentar = forms.CharField(required=False, max_length=20)


class VotacaoNominalForm(forms.Form):
    pass


class ListMateriaForm(forms.Form):
    error_message = forms.CharField(required=False, label='votacao_aberta')


class MesaForm(forms.Form):
    parlamentar = forms.IntegerField(required=True)
    cargo = forms.IntegerField(required=True)


class ExpedienteForm(forms.Form):
    conteudo = forms.CharField(required=False, widget=forms.Textarea)


class VotacaoForm(forms.Form):
    votos_sim = forms.CharField(required=True, label='Sim')
    votos_nao = forms.CharField(required=True, label='Não')
    abstencoes = forms.CharField(required=True, label='Abstenções')
    total_votos = forms.CharField(required=False, label='total')


class VotacaoEditForm(forms.Form):
    pass


class SessaoPlenariaFilterSet(django_filters.FilterSet):

    data_inicio__year = django_filters.ChoiceFilter(required=False,
                                                    label='Ano',
                                                    choices=ANO_CHOICES)
    data_inicio__month = django_filters.ChoiceFilter(required=False,
                                                     label='Mês',
                                                     choices=MES_CHOICES)
    data_inicio__day = django_filters.ChoiceFilter(required=False,
                                                   label='Dia',
                                                   choices=DIA_CHOICES)
    titulo = _('Pesquisa de Sessão Plenária')

    class Meta:
        model = SessaoPlenaria
        fields = ['tipo']

    def __init__(self, *args, **kwargs):
        super(SessaoPlenariaFilterSet, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('data_inicio__year', 3),
             ('data_inicio__month', 3),
             ('data_inicio__day', 3),
             ('tipo', 3)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(self.titulo,
                     row1,
                     form_actions(save_label='Pesquisar'))
        )


class AdicionarVariasMateriasFilterSet(MateriaLegislativaFilterSet):

    o = MateriaPesquisaOrderingFilter()

    class Meta:
        model = MateriaLegislativa
        fields = ['numero',
                  'numero_protocolo',
                  'ano',
                  'tipo',
                  'data_apresentacao',
                  'data_publicacao',
                  'autoria__autor__tipo',
                  # FIXME 'autoria__autor__partido',
                  'relatoria__parlamentar_id',
                  'local_origem_externa',
                  'em_tramitacao',
                  ]

    def __init__(self, *args, **kwargs):
        super(MateriaLegislativaFilterSet, self).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['autoria__autor__tipo'].label = 'Tipo de Autor'
        # self.filters['autoria__autor__partido'].label = 'Partido do Autor'
        self.filters['relatoria__parlamentar_id'].label = 'Relatoria'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('numero_protocolo', 4)])
        row3 = to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row4 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        row5 = to_row(
            [('autoria__autor__tipo', 6),
             # ('autoria__autor__partido', 6)
             ])
        row6 = to_row(
            [('relatoria__parlamentar_id', 6),
             ('local_origem_externa', 6)])
        row7 = to_row(
            [('em_tramitacao', 6),
             ('o', 6)])
        row8 = to_row(
            [('ementa', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria'),
                     row1, row2, row3,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row4, row5, row6, row7, row8,
                     form_actions(save_label='Pesquisar'))
        )


class OradorForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(OradorForm, self).__init__(*args, **kwargs)

        id_sessao = int(self.initial['id_sessao'])

        ids = [s.parlamentar.id for
               s in SessaoPlenariaPresenca.objects.filter(
                   sessao_plenaria_id=id_sessao)]

        self.fields['parlamentar'].queryset = Parlamentar.objects.filter(
            id__in=ids).order_by('nome_completo')

    class Meta:
        model = Orador
        exclude = ['sessao_plenaria']


class OradorExpedienteForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(OradorExpedienteForm, self).__init__(*args, **kwargs)

        self.fields['parlamentar'].queryset = Parlamentar.objects.filter(
            ativo=True).order_by('nome_completo')

    class Meta:
        model = OradorExpediente
        exclude = ['sessao_plenaria']


class PautaSessaoFilterSet(SessaoPlenariaFilterSet):
    titulo = _('Pesquisa de Pauta de Sessão')


class ResumoOrdenacaoForm(forms.Form):
    primeiro = forms.ChoiceField(label=_('1°'),
                                 choices=ORDENACAO_RESUMO)
    segundo = forms.ChoiceField(label=_('2°'),
                                choices=ORDENACAO_RESUMO)
    terceiro = forms.ChoiceField(label='3°',
                                 choices=ORDENACAO_RESUMO)
    quarto = forms.ChoiceField(label=_('4°'),
                               choices=ORDENACAO_RESUMO)
    quinto = forms.ChoiceField(label=_('5°'),
                               choices=ORDENACAO_RESUMO)
    sexto = forms.ChoiceField(label=_('6°'),
                              choices=ORDENACAO_RESUMO)
    setimo = forms.ChoiceField(label=_('7°'),
                               choices=ORDENACAO_RESUMO)
    oitavo = forms.ChoiceField(label=_('8°'),
                               choices=ORDENACAO_RESUMO)
    nono = forms.ChoiceField(label=_('9°'),
                             choices=ORDENACAO_RESUMO)
    decimo = forms.ChoiceField(label='10°',
                               choices=ORDENACAO_RESUMO)

    def __init__(self, *args, **kwargs):
        super(ResumoOrdenacaoForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('primeiro', 12)])
        row2 = to_row(
            [('segundo', 12)])
        row3 = to_row(
            [('terceiro', 12)])
        row4 = to_row(
            [('quarto', 12)])
        row5 = to_row(
            [('quinto', 12)])
        row6 = to_row(
            [('sexto', 12)])
        row7 = to_row(
            [('setimo', 12)])
        row8 = to_row(
            [('oitavo', 12)])
        row9 = to_row(
            [('nono', 12)])
        row10 = to_row(
            [('decimo', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_(''),
                     row1, row2, row3, row4, row5,
                     row6, row7, row8, row9, row10,
                     form_actions(save_label='Atualizar'))
        )

    def clean(self):
        super(ResumoOrdenacaoForm, self).clean()

        cleaned_data = self.cleaned_data

        for c1 in cleaned_data:
            i = 0
            for c2 in cleaned_data:
                if cleaned_data[str(c1)] == cleaned_data[str(c2)]:
                    i = i + 1
                    if i > 1:
                        raise ValidationError(_(
                            'Não é possível ter campos repetidos'))
