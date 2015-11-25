from django import forms
from django.utils.translation import ugettext_lazy as _
from vanilla import GenericView

from sapl.crud import build_crud

from .models import (CargoMesa, Coligacao, Dependente, Filiacao, Legislatura,
                     Mandato, NivelInstrucao, Parlamentar, Partido,
                     SessaoLegislativa, SituacaoMilitar, TipoAfastamento,
                     TipoDependente)

cargo_mesa_crud = build_crud(
    CargoMesa, 'cargo_mesa', [

        [_('Cargo na Mesa'),
         [('descricao', 10),
            ('unico', 2)]],
    ])

legislatura_crud = build_crud(
    Legislatura, 'tabelas_auxiliares#legislatura', [

        [_('Legislatura'),
         [('id', 3),
            ('data_inicio', 2),
            ('data_fim', 2),
            ('data_eleicao', 2)],
            [('data_inicio', 4), ('data_fim', 4), ('data_eleicao', 4)]],
    ])

coligacao_crud = build_crud(
    Coligacao, 'coligacao', [

        [_('Coligação'),
         [('nome', 5),
            ('legislatura', 5),
            ('numero_votos', 2)]],
    ])

partido_crud = build_crud(
    Partido, 'partidos', [

        [_('Partido Político'),
         [('nome', 6),
            ('sigla', 2),
            ('data_criacao', 2),
            ('data_extincao', 2)]],
    ])


dependente_crud = build_crud(
    Dependente, '', [

        [_('Dependentes'),
         [('nome', 12)],
            [('tipo', 4), ('sexo', 4), ('data_nascimento', 4)],
            [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)]],
    ])


sessao_legislativa_crud = build_crud(
    SessaoLegislativa, 'sessao_legislativa', [

        [_('Sessão Legislativa'),
         [('numero', 2),
            ('tipo', 2),
            ('data_inicio', 2),
            ('data_fim', 2),
            ('data_inicio_intervalo', 2),
            ('data_fim_intervalo', 2)]],
    ])


parlamentar_crud = build_crud(
    Parlamentar, '', [

        [_('Cadastro do Parlamentar'),
         [('nome_parlamentar', 8), ('ativo', 4)],
            [('nome_completo', 12)],
            [('nivel_instrucao', 4), ('sexo', 4), ('data_nascimento', 4)],
            [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)],
            [('situacao_militar', 6), ('profissao', 6)],
            [('endereco_web', 12)],
            [('email', 12)],
            [('numero_gab_parlamentar', 4), ('telefone', 4), ('fax', 4)],
            [('endereco_residencia', 6), ('cep_residencia', 6)],
            [('municipio_residencia', 12)],
            [('telefone_residencia', 6), ('fax_residencia', 6)],
            [('locais_atuacao', 12)],
            [('fotografia', 12)],
            [('biografia', 12)]],
    ])

filiacao_crud = build_crud(
    Filiacao, '', [

        [_('Filiações Partidárias '),
         [('partido', 4), ('data', 4), ('data_desfiliacao', 4)]],
    ])

mandato_crud = build_crud(
    Mandato, '', [

        [_('Mandato'),
         [('legislatura', 4), ('coligacao', 4), ('votos_recebidos', 4)],
            [('ind_titular_FIXME', 3),
             ('dat_inicio_mandato_FIXME', 3),
             ('data_fim_mandato', 3),
             ('data_expedicao_diploma', 3)],
            [('observacao', 12)]],
    ])

tipo_dependente_crud = build_crud(
    TipoDependente, 'tipo_dependente', [

        [_('Tipo de Dependente'),
         [('descricao', 12)]],
    ])

nivel_instrucao_crud = build_crud(
    NivelInstrucao, 'nivel_instrucao', [

        [_('Nível Instrução'),
         [('descricao', 12)]],
    ])

tipo_afastamento_crud = build_crud(
    TipoAfastamento, 'tipo_afastamento', [

        [_('Tipo de Afastamento'),
         [('descricao', 5), ('dispositivo', 5), ('afastamento', 2)]],
    ])

tipo_militar_crud = build_crud(
    SituacaoMilitar, 'tipo_situa_militar', [

        [_('Tipo Situação Militar'),
         [('descricao', 12)]],
    ])


class ParlamentaresForm(forms.Form):
    periodo = forms.CharField()


class ParlamentaresView(GenericView):
    template_name = "parlamentares/parlamentares_list.html"

    def get(self, request, *args, **kwargs):
        form = ParlamentaresForm()
        legislaturas = Legislatura.objects.all().order_by(
            '-data_inicio', '-data_fim')
        return self.render_to_response(
            {'legislaturas': legislaturas,
             'legislatura_id': legislaturas.first().id,
             'mandatos': Mandato.objects.all(),
             'form': form,
             'filiacao': Filiacao.objects.all()})

    def post(self, request, *args, **kwargs):
        form = ParlamentaresForm(request.POST)
        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all().order_by(
                '-data_inicio', '-data_fim'),
             'legislatura_id': int(form.data['periodo']),
             'mandatos': Mandato.objects.all(),
             'form': form,
             'filiacao': Filiacao.objects.all()})
