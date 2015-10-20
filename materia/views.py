from datetime import date, datetime
from django.utils.translation import ugettext_lazy as _

from sapl.crud import build_crud

from django import forms
from django.views.generic.edit import FormMixin

from .models import (Anexada, Autor, Autoria, DocumentoAcessorio,
                     MateriaLegislativa, Numeracao, Orgao, Origem, Proposicao,
                     RegimeTramitacao, Relatoria, StatusTramitacao, TipoAutor,
                     TipoDocumento, TipoFimRelatoria, TipoMateriaLegislativa,
                     TipoProposicao, Tramitacao, UnidadeTramitacao)

from vanilla import GenericView

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

def get_tipos_materia():
    return [('', 'Selecione')] \
        + [(t.id, t.sigla + ' - ' + t.descricao)
           for t in TipoMateriaLegislativa.objects.all()]

def get_range_anos():
    return [('', 'Selecione')] \
        + [(year, year) for year in range(date.today().year, 1960, -1)]

def get_regimes_tramitacao():
    return [('1', 'Normal'),
            ('3', 'Urgência'),
            ('4', 'Urgência Especial')]  


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))

class FormularioSimplificadoForm(forms.Form):

    tipo_materia = forms.ChoiceField(required=True,
                                     label='Tipo Matéria',
                                     choices=get_tipos_materia(),
                                     widget=forms.Select(
                                         attrs={'class': 'selector'}))

    numero_materia = forms.CharField(
        label='Núm. Matéria', required=True)

    ano_materia = forms.ChoiceField(required=True,
                            label='Ano',
                            choices=get_range_anos(),
                            widget=forms.Select(
                                attrs={'class': 'selector'}))

    data_materia = forms.DateField(label='Data Apresentação',
                              required=True,
                              widget=forms.TextInput(
                                  attrs={'class': 'dateinput'}))                                    

    numero_protocolo = forms.CharField(
        label='Número de Protocolo', required=True)

    regime_tramitacao = forms.ChoiceField(required=False,
                            label='Regime de Tramitação',
                            choices=get_regimes_tramitacao(),
                            widget=forms.Select(
                            attrs={'class': 'selector'}))

    em_tramitacao = forms.TypedChoiceField(
                   coerce=lambda x: x == 'Sim',
                   choices=((True, 'Sim'), (False, 'Não')),
                   widget=forms.RadioSelect
                )

    ementa = forms.CharField(label='Ementa', required=True, widget=forms.Textarea)

    texto_original = forms.ChoiceField(required=False,
                        label='Regime de Tramitação',
                        choices=(('1', 'Arquivo'), ('2', 'Proposição')),
                        widget=forms.RadioSelect)

    arquivo = forms.FileField(required=False, label='Arquivo')    

    proposicao = forms.CharField(required=False, label='Proposição',
        widget=forms.TextInput(attrs={'disabled':'True'}))
    
# form.fields['otherFields'].widget.attrs['enabled'] = True

class FormularioSimplificadoView(FormMixin, GenericView):

    template_name = "materia/formulario_simplificado.html"

    def get(self, request, *args, **kwargs):
        form = FormularioSimplificadoForm()
        return self.render_to_response({'form': form})    

