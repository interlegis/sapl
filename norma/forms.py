from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext as _

from .models import (AssuntoNorma, TipoNormaJuridica, NormaJuridica,
                     LegislacaoCitada)
from sapl.layout import SaplFormLayout


class AssuntoNormaForm(forms.ModelForm):

    class Meta:
        model = AssuntoNorma
        exclude = []

    def __init__(self, *args, **kwargs):
        super(AssuntoNormaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Assunto Norma Jurídica'),
             [('assunto', 4), ('assunto', 4), ('descricao', 4)],
             [('assunto', 12)],
             [('descricao', 12)]],
        )


class TipoNormaJuridicaForm(forms.ModelForm):

    class Meta:
        model = TipoNormaJuridica
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoNormaJuridicaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo Norma Jurídica'),
             [('descricao', 3),
              ('descricao', 3),
              ('sigla', 3),
              ('equivalente_lexml', 3)],
             [('descricao', 4), ('sigla', 4), ('equivalente_lexml', 4)]],
        )


class NormaJuridicaForm(forms.ModelForm):

    class Meta:
        model = NormaJuridica
        exclude = []

    def __init__(self, *args, **kwargs):
        super(NormaJuridicaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Identificação Básica'),
             [('tipo', 4), ('numero', 4), ('ano', 4)],
             [('data', 4), ('esfera_federacao', 4), ('complemento', 4)],
             [('tip_id_basica_FIXME', 4),
              ('num_ident_basica_FIXME', 4),
              ('ano_ident_basica_FIXME', 4)],
             [('data_publicacao', 3),
              ('veiculo_publicacao', 3),
              ('pagina_inicio_publicacao', 3),
              ('pagina_fim_publicacao', 3)],
             [('file_FIXME', 6), ('tip_situacao_norma_FIXME', 6)],
             [('ementa', 12)],
             [('indexacao', 12)],
             [('observacao', 12)]],

            [_('Assuntos (Classificação) [+] '),
             [('assunto_norma_FIXME', 12)],
             [('assunto_norma_FIXME', 12)],
             [('assunto_norma_FIXME', 12)]],
        )


class LegislacaoCitadaForm(forms.ModelForm):

    class Meta:
        model = LegislacaoCitada
        exclude = []

    def __init__(self, *args, **kwargs):
        super(LegislacaoCitadaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Legislação Citada'),
             [('tip_norma_FIXME', 4),
              ('num_norma_FIXME', 4),
              ('ano_norma_FIXME', 4)],
             [('disposicoes', 3), ('parte', 3), ('livro', 3), ('titulo', 3)],
             [('capitulo', 3), ('secao', 3), ('subsecao', 3), ('artigo', 3)],
             [('paragrafo', 3), ('inciso', 3), ('alinea', 3), ('item', 3)]],
        )
