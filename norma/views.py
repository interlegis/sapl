from datetime import datetime
from re import sub

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin
from vanilla.views import GenericView

import sapl
from sapl.layout import form_actions
from compilacao.views import IntegracaoTaView
from materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.crud import build_crud

from .models import (AssuntoNorma, LegislacaoCitada, NormaJuridica,
                     TipoNormaJuridica)

assunto_norma_crud = build_crud(
    AssuntoNorma, 'assunto_norma_juridica', [

        [_('Assunto Norma Jurídica'),
         [('assunto', 6), ('descricao', 6)]],
    ])

tipo_norma_crud = build_crud(
    TipoNormaJuridica, 'tipo_norma_juridica', [

        [_('Tipo Norma Jurídica'),
         [('descricao', 4),
            ('sigla', 4),
            ('equivalente_lexml', 4)]],
    ])

norma_crud = build_crud(

    NormaJuridica, '', [

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
    ])

norma_temporario_crud = build_crud(
    NormaJuridica, 'normajuridica', [

        [_('Identificação Básica'),
         [('tipo', 5), ('numero', 2), ('ano', 2), ('data', 3)],
            [('ementa', 12)]],
    ])


legislacao_citada_crud = build_crud(
    LegislacaoCitada, '', [

        [_('Legislação Citada'),
         [('tip_norma_FIXME', 4),
            ('num_norma_FIXME', 4),
            ('ano_norma_FIXME', 4)],
            [('disposicoes', 3), ('parte', 3), ('livro', 3), ('titulo', 3)],
            [('capitulo', 3), ('secao', 3), ('subsecao', 3), ('artigo', 3)],
            [('paragrafo', 3), ('inciso', 3), ('alinea', 3), ('item', 3)]],
    ])


def get_esferas():
    return [('E', 'Estadual'),
            ('F', 'Federal'),
            ('M', 'Municipal')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class NormaJuridicaForm(ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label='Matéria Legislativa',
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione'
        )

    numero_materia = forms.CharField(label='Número', required=False)

    ano_materia = forms.CharField(label='Ano', required=False)

    class Meta:
        model = NormaJuridica
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data',
                  'esfera_federacao',
                  'complemento',
                  'tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'data_publicacao',
                  'veiculo_publicacao',
                  'pagina_inicio_publicacao',
                  'pagina_fim_publicacao',
                  'ementa',
                  'indexacao',
                  'observacao',
                  'texto_integral']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])

        row2 = sapl.layout.to_row(
            [('data', 4),
             ('esfera_federacao', 4),
             ('complemento', 4)])

        row3 = sapl.layout.to_row(
            [('tipo_materia', 4),
             ('numero_materia', 4),
             ('ano_materia', 4)])

        row4 = sapl.layout.to_row(
            [('data_publicacao', 3),
             ('veiculo_publicacao', 3),
             ('pagina_inicio_publicacao', 3),
             ('pagina_fim_publicacao', 3)])

        row5 = sapl.layout.to_row(
            [('texto_integral', 12)])

        row6 = sapl.layout.to_row(
            [('ementa', 12)])

        row7 = sapl.layout.to_row(
            [('indexacao', 12)])

        row8 = sapl.layout.to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Cadastro de Norma Jurídica',
                     Fieldset('Identificação Básica',
                              row1, row2, row3, row4, row5, row6, row7, row8),
                     form_actions()
                     )
        )
        super(NormaJuridicaForm, self).__init__(*args, **kwargs)


class NormaIncluirView(FormMixin, GenericView):
    template_name = "norma/normajuridica_incluir.html"

    def get_success_url(self):
        return '/norma/'

    def get(self, request, *args, **kwargs):
        form = NormaJuridicaForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = NormaJuridicaForm(request.POST or None)
        if form.is_valid():
            norma = form.save(commit=False)

            if form.cleaned_data['tipo_materia']:
                tipo = TipoMateriaLegislativa.objects.get(
                    id=form.cleaned_data['tipo_materia'])
                try:
                    materia = MateriaLegislativa.objects.get(
                        tipo=tipo,
                        numero=form.cleaned_data['numero'],
                        ano=form.cleaned_data['ano'])
                except ObjectDoesNotExist:
                    return self.render_to_response(
                        {'form': form,
                         'error': 'Matéria adicionada não existe!'})
                else:
                    norma.materia = materia

            if form.cleaned_data['indexacao']:
                norma.indexacao = sub(
                    '&nbsp;', ' ', strip_tags(form.cleaned_data['indexacao']))

            if form.cleaned_data['observacao']:
                norma.observacao = sub(
                    '&nbsp;', ' ', strip_tags(form.cleaned_data['observacao']))

            if 'texto_integral' in request.FILES:
                norma.texto_integral = request.FILES['texto_integral']

            norma.ementa = sub(
                '&nbsp;', ' ', strip_tags(form.cleaned_data['ementa']))
            norma.timestamp = datetime.now()
            norma.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class NormaTaView(IntegracaoTaView):
    model = NormaJuridica
