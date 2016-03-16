from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Fieldset, Layout, Submit
from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions

from .models import Dependente, Filiacao, Mandato, Parlamentar, Legislatura


class ParlamentaresListForm(forms.Form):
    periodo = forms.CharField()


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class ParlamentaresForm (ModelForm):
    ativo = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, 'Sim'), (False, 'Não')),
        widget=forms.RadioSelect(
            renderer=HorizontalRadioRenderer
        )
    )

    class Meta:
        model = Parlamentar
        fields = ['nome_parlamentar',
                  'ativo',
                  'nome_completo',
                  'nivel_instrucao',
                  'sexo',
                  'cpf',
                  'rg',
                  'titulo_eleitor',
                  'data_nascimento',
                  'situacao_militar',
                  'profissao',
                  'endereco_web',
                  'email',
                  'numero_gab_parlamentar',
                  'telefone',
                  'fax',
                  'endereco_residencia',
                  'cep_residencia',
                  'municipio_residencia',
                  'telefone_residencia',
                  'fax_residencia',
                  'locais_atuacao',
                  'fotografia',
                  'biografia']

        widgets = {
            'cpf': forms.TextInput(attrs={'class': 'cpf'}),
            'rg': forms.TextInput(attrs={'class': 'rg'}),
            'titulo_eleitor': forms.TextInput(attrs={
              'class': 'titulo_eleitor'}),
            'telefone': forms.TextInput(attrs={'class': 'telefone'}),
            'fax': forms.TextInput(attrs={'class': 'telefone'}),
            'cep_residencia': forms.TextInput(attrs={'class': 'cep'}),
            'telefone_residencia': forms.TextInput(attrs={
              'class': 'telefone'}),
            'fax_residencia': forms.TextInput(attrs={'class': 'telefone'}),
            'fotografia': forms.FileInput,
            'biografia': forms.Textarea(attrs={'id': 'biografia-parlamentar'})
        }

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('nome_parlamentar', 8), ('ativo', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('nome_completo', 12)])

        row3 = crispy_layout_mixin.to_row(
            [('nivel_instrucao', 4),
             ('sexo', 4),
             ('data_nascimento', 4)])

        row4 = crispy_layout_mixin.to_row(
            [('cpf', 4),
             ('rg', 4),
             ('titulo_eleitor', 4)])

        row5 = crispy_layout_mixin.to_row(
            [('situacao_militar', 6),
             ('profissao', 6)])

        row6 = crispy_layout_mixin.to_row(
            [('endereco_web', 12)])

        row7 = crispy_layout_mixin.to_row(
            [('email', 12)])

        row8 = crispy_layout_mixin.to_row(
            [('numero_gab_parlamentar', 4),
             ('telefone', 4),
             ('fax', 4)])

        row9 = crispy_layout_mixin.to_row(
            [('endereco_residencia', 6),
             ('cep_residencia', 6)])

        row10 = crispy_layout_mixin.to_row(
            [('municipio_residencia', 12)])

        row11 = crispy_layout_mixin.to_row(
            [('telefone_residencia', 6),
             ('fax_residencia', 6)])

        row12 = crispy_layout_mixin.to_row(
            [('locais_atuacao', 12)])

        row13 = crispy_layout_mixin.to_row(
            [('fotografia', 12)])

        row14 = crispy_layout_mixin.to_row(
            [('biografia', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Cadastro do Parlamentar'),
                     row1, row2, row3, row4, row5,
                     row6, row7, row8, row9, row10,
                     row11, row12, row13,
                     HTML("""{% if form.fotografia.value %}
                        <img class="img-responsive" width="225" height="300"
                             src="{{ MEDIA_URL }}{{ form.fotografia.value }}">
                             <br /><br />
                        <input type="submit"
                               name="remover"
                               id="remover"
                               class="btn btn-warning"
                               value="Remover Foto"/>
                         {% endif %}""", ),
                     row14,
                     form_actions())

        )
        super(ParlamentaresForm, self).__init__(
            *args, **kwargs)


class ParlamentaresEditForm(ParlamentaresForm):

    def __init__(self, *args, **kwargs):
        super(ParlamentaresEditForm, self).__init__(
            *args, **kwargs)

        self.helper.layout[0][-1:] = form_actions(more=[
            HTML('&nbsp;'),
            Submit('excluir', 'Excluir',
                   css_class='btn btn-primary')])


class MandatoForm(ModelForm):

    legislatura = forms.ModelChoiceField(
        label=_('Legislatura'),
        required=False,
        queryset=Legislatura.objects.all().order_by('-data_inicio'),
        empty_label='----------',
    )

    class Meta:
        model = Mandato
        fields = ['legislatura',
                  'coligacao',
                  'votos_recebidos',
                  'data_fim_mandato',
                  'data_expedicao_diploma',
                  'observacao']

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('legislatura', 4),
             ('coligacao', 4),
             ('votos_recebidos', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('data_fim_mandato', 6),
             ('data_expedicao_diploma', 6)])

        row3 = crispy_layout_mixin.to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Adicionar Mandato'), row1, row2, row3,
                     form_actions())

        )
        super(MandatoForm, self).__init__(
            *args, **kwargs)


class MandatoEditForm(MandatoForm):

    def __init__(self, *args, **kwargs):
        super(MandatoEditForm, self).__init__(
            *args, **kwargs)

        self.helper.layout[0][-1:] = form_actions(more=[
            HTML('&nbsp;'),
            Submit('excluir', 'Excluir',
                   css_class='btn btn-primary')])


class DependenteForm(ModelForm):

    class Meta:
        model = Dependente
        fields = ['nome',
                  'data_nascimento',
                  'tipo',
                  'sexo',
                  'cpf',
                  'rg',
                  'titulo_eleitor']

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('nome', 12)])

        row2 = crispy_layout_mixin.to_row(
            [('tipo', 4),
             ('sexo', 4),
             ('data_nascimento', 4)])

        row3 = crispy_layout_mixin.to_row(
            [('cpf', 4),
             ('rg', 4),
             ('titulo_eleitor', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Cadastro de Dependentes'),
                     row1, row2, row3,
                     form_actions())

        )
        super(DependenteForm, self).__init__(
            *args, **kwargs)


class DependenteEditForm(DependenteForm):

    def __init__(self, *args, **kwargs):
        super(DependenteEditForm, self).__init__(
            *args, **kwargs)

        self.helper.layout[0][-1:] = form_actions(more=[
            HTML('&nbsp;'),
            Submit('excluir', 'Excluir',
                   css_class='btn btn-primary')])


class FiliacaoForm(ModelForm):

    class Meta:
        model = Filiacao
        fields = ['partido',
                  'data',
                  'data_desfiliacao']

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('partido', 4),
             ('data', 4),
             ('data_desfiliacao', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Adicionar Filiação'), row1,
                     form_actions())

        )
        super(FiliacaoForm, self).__init__(
            *args, **kwargs)


class FiliacaoEditForm(FiliacaoForm):

    def __init__(self, *args, **kwargs):
        super(FiliacaoEditForm, self).__init__(
            *args, **kwargs)

        self.helper.layout[0][-1:] = form_actions(more=[
            HTML('&nbsp;'),
            Submit('excluir', 'Excluir',
                   css_class='btn btn-primary')])
