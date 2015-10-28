from django.utils.translation import ugettext_lazy as _

from sapl.crud import build_crud

from django import forms
from django.utils.safestring import mark_safe

from django.core.urlresolvers import reverse

from datetime import datetime

from .models import (AssuntoNorma, LegislacaoCitada, NormaJuridica,
                     TipoNormaJuridica)

from materia.models import TipoMateriaLegislativa

from django.views.generic.edit import FormMixin
from vanilla import GenericView

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

        [_('Assuntos (Classificação) [+] '),
         [('assunto_norma_FIXME', 12)],
            [('assunto_norma_FIXME', 12)],
            [('assunto_norma_FIXME', 12)]],
    ])

norma_temporario_para_compilacao_crud = build_crud(
    NormaJuridica, 'norma', [

        [_('Identificação Básica'),
         [('tipo', 4), ('numero', 4), ('ano', 4)],
            [('data', 4), ('esfera_federacao', 4)],
            [('data_publicacao', 3)],
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


def get_tipos_norma():
    return [('', 'Selecione')] \
        + [(n.id, n.descricao)
           for n in TipoNormaJuridica.objects.all()]

def get_esferas():
    return [('E', 'Estadual'),
            ('F', 'Federal'),
            ('M', 'Municipal')]

def get_tipos_materia():
    return [('', 'Selecione')] \
        + [(t.id, t.sigla + ' - ' + t.descricao)
           for t in TipoMateriaLegislativa.objects.all()]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))

class NormaJuridicaForm(forms.Form):

    tipo = forms.ChoiceField(required=True,
                             label='Tipo',
                             choices= get_tipos_norma(),
                             widget=forms.Select(
                                 attrs={'class': 'selector'}))

    numero = forms.CharField(label='Número', required=True)

    ano = forms.CharField(label='Ano', required=True)

    data = forms.DateField(label='Data',
                                    required=True,
                                    input_formats=['%d/%m/%Y'],
                                    widget=forms.TextInput(
                                        attrs={'class': 'dateinput'}))

    esfera = forms.ChoiceField(required=True,
                             label='Tipo',
                             choices=get_esferas(),
                             widget=forms.Select(
                                 attrs={'class': 'selector'}))

    complementar = forms.ChoiceField(required=False,
                                  choices=[('1', 'Sim'), ('0', 'Não')],
                                  widget=forms.RadioSelect(
                                      renderer=HorizontalRadioRenderer),
                                  label='Complementar')

    materia = forms.ChoiceField(required=False,
                             label='Materia Legislativa',
                             choices=get_tipos_materia(),
                             widget=forms.Select(
                                 attrs={'class': 'selector'}))

    numero_materia = forms.CharField(label='Número', required=False)

    ano_materia = forms.CharField(label='Ano', required=False)    

    data_publicacao = forms.DateField(label='Data Publicação',
                                       required=False,
                                       input_formats=['%d/%m/%Y'],
                                       widget=forms.TextInput(
                                           attrs={'class': 'dateinput'}))

    veiculo_publicacao = forms.CharField(label='Veiculo Publicação', required=False)

    pg_inicio = forms.CharField(label='Pg. Início', required=False)

    pg_fim = forms.CharField(label='Pg. Fim', required=False)

    # texto = form.FileUpload(label='Texto', required=False) # TODO: implement file upload

    data_fim_vigencia =  forms.DateField(label='Data Fim Vigência',
                                       required=False,
                                       input_formats=['%d/%m/%Y'],
                                       widget=forms.TextInput(
                                           attrs={'class': 'dateinput'}))

    ementa = forms.CharField(label='Ementa', required=True, widget=forms.Textarea)

    indexacao = forms.CharField(label='Indexação', required=False, widget=forms.Textarea)

    observacao = forms.CharField(label='Observação', required=False, widget=forms.Textarea)

class NormaIncluirView(FormMixin, GenericView):
    template_name = "norma/normajuridica_incluir.html"

    def get_success_url(self):
        return reverse('norma-incluir')

    def get(self, request, *args, **kwargs):
        form = NormaJuridicaForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):

        form = NormaJuridicaForm(request.POST or None)

        if form.is_valid():

            norma = NormaJuridica()
            norma.tipo = TipoNormaJuridica.objects.get(id=form.cleaned_data['tipo'])
            norma.numero = form.cleaned_data['numero']
            norma.ano = form.cleaned_data['ano']
            norma.data = form.cleaned_data['data']
            norma.esfera = form.cleaned_data['esfera']
            norma.complementar = form.cleaned_data['complementar']
            if form.cleaned_data['complementar']:
               norma.complementar = TipoMateriaLegislativa.objects.get(id=form.cleaned_data['complementar'])

            if form.cleaned_data['materia']:
                norma.materia = form.cleaned_data['materia']

            if form.cleaned_data['numero_materia']:
                norma.numero_materia = form.cleaned_data['numero_materia']

            if form.cleaned_data['ano_materia']:
                norma.ano_materia = form.cleaned_data['ano_materia']

            if form.cleaned_data['data_publicacao']:
                norma.data_publicacao = form.cleaned_data['data_publicacao']

            if form.cleaned_data['veiculo_publicacao']:
                norma.veiculo_publicacao = form.cleaned_data['veiculo_publicacao']

            if form.cleaned_data['pg_inicio']:
                norma.pg_inicio = form.cleaned_data['pg_inicio']

            if form.cleaned_data['pg_fim']:
                norma.pg_fim = form.cleaned_data['pg_fim']

            if form.cleaned_data['data_fim_vigencia']:
                norma.data_fim_vigencia = form.cleaned_data['data_fim_vigencia']

            norma.ementa = form.cleaned_data['ementa']

            norma.indexacao = form.cleaned_data['indexacao']

            norma.observacao = form.cleaned_data['observacao']

            norma.timestamp = datetime.now()

            norma.save()

            return self.render_to_response({'form': form})
        else:
            return self.form_invalid(form)


