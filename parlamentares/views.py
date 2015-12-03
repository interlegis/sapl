from re import sub

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, ButtonHolder, Fieldset, Layout, Submit
from django import forms
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin
from vanilla import GenericView

import sapl
from sapl.crud import build_crud

from .models import (CargoMesa, Coligacao, ComposicaoMesa, Dependente,
                     Filiacao, Legislatura, Mandato, NivelInstrucao,
                     Parlamentar, Partido, SessaoLegislativa, SituacaoMilitar,
                     TipoAfastamento, TipoDependente)

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


class ParlamentaresListForm(forms.Form):
    periodo = forms.CharField()


class ParlamentaresView(GenericView):
    template_name = "parlamentares/parlamentares_list.html"

    def get(self, request, *args, **kwargs):
        form = ParlamentaresListForm()
        legislaturas = Legislatura.objects.all().order_by(
            '-data_inicio', '-data_fim')
        return self.render_to_response(
            {'legislaturas': legislaturas,
             'legislatura_id': legislaturas.first().id,
             'mandatos': Mandato.objects.all(),
             'form': form,
             'filiacao': Filiacao.objects.all()})

    def post(self, request, *args, **kwargs):
        form = ParlamentaresListForm(request.POST)
        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all().order_by(
                '-data_inicio', '-data_fim'),
             'legislatura_id': int(form.data['periodo']),
             'mandatos': Mandato.objects.all(),
             'form': form,
             'filiacao': Filiacao.objects.all()})


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

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('nome_parlamentar', 8), ('ativo', 4)])

        row2 = sapl.layout.to_row(
            [('nome_completo', 12)])

        row3 = sapl.layout.to_row(
            [('nivel_instrucao', 4),
             ('sexo', 4),
             ('data_nascimento', 4)])

        row4 = sapl.layout.to_row(
            [('cpf', 4),
             ('rg', 4),
             ('titulo_eleitor', 4)])

        row5 = sapl.layout.to_row(
            [('situacao_militar', 6),
             ('profissao', 6)])

        row6 = sapl.layout.to_row(
            [('endereco_web', 12)])

        row7 = sapl.layout.to_row(
            [('email', 12)])

        row8 = sapl.layout.to_row(
            [('numero_gab_parlamentar', 4),
             ('telefone', 4),
             ('fax', 4)])

        row9 = sapl.layout.to_row(
            [('endereco_residencia', 6),
             ('cep_residencia', 6)])

        row10 = sapl.layout.to_row(
            [('municipio_residencia', 12)])

        row11 = sapl.layout.to_row(
            [('telefone_residencia', 6),
             ('fax_residencia', 6)])

        row12 = sapl.layout.to_row(
            [('locais_atuacao', 12)])

        row13 = sapl.layout.to_row(
            [('fotografia', 12)])

        row14 = sapl.layout.to_row(
            [('biografia', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Cadastro do Parlamentar',
                     row1, row2, row3, row4, row5,
                     row6, row7, row8, row9, row10,
                     row11, row12, row13, row14,
                     ButtonHolder(
                         Submit('submit', 'Salvar',
                                css_class='button primary'),
                     ))

        )
        super(ParlamentaresForm, self).__init__(
            *args, **kwargs)


class ParlamentaresEditForm(ParlamentaresForm):

    def __init__(self, *args, **kwargs):
        super(ParlamentaresEditForm, self).__init__(
            *args, **kwargs)

        self.helper.layout[0][-1:] = ButtonHolder(
            Submit('salvar', 'Salvar',
                   css_class='button primary'),
            HTML('&nbsp;'),
            Submit('excluir', 'Excluir',
                   css_class='button primary'),)


class ParlamentaresCadastroView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_cadastro.html"

    def get_success_url(self):
        return reverse('parlamentares')

    def get(self, request, *args, **kwargs):
        form = ParlamentaresForm()
        pk = kwargs['pk']
        return self.render_to_response({'form': form, 'legislatura_id': pk})

    def post(self, request, *args, **kwargs):
        form = ParlamentaresForm(request.POST)

        pk = kwargs['pk']

        if form.is_valid():
            parlamentar = form.save(commit=False)
            if 'fotografia' in request.FILES:
                parlamentar.fotografia = request.FILES['fotografia']
                parlamentar.biografia = sub('&nbsp;',
                                            ' ',
                                            strip_tags(form.data['biografia']))
                parlamentar.save()

                mandato = Mandato()

                mandato.parlamentar = parlamentar
                mandato.legislatura = Legislatura.objects.get(id=pk)
                mandato.save()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form, 'legislatura_id': pk})


class ParlamentaresEditarView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_cadastro.html"

    def get_success_url(self):
        return reverse('parlamentares')

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        pid = kwargs['pid']
        parlamentar = Parlamentar.objects.get(id=pid)

        form = ParlamentaresEditForm(instance=parlamentar)
        return self.render_to_response({'form': form, 'legislatura_id': pk})

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        pid = kwargs['pid']
        parlamentar = Parlamentar.objects.get(id=pid)
        form = ParlamentaresEditForm(request.POST, instance=parlamentar)

        if form.is_valid():
            if 'salvar' in request.POST:
                parlamentar = form.save(commit=False)
                if 'fotografia' in request.FILES:
                    parlamentar.fotografia = request.FILES['fotografia']
                parlamentar.biografia = sub('&nbsp;',
                                            ' ',
                                            strip_tags(form.data['biografia']))
                parlamentar.save()
            elif 'excluir' in request.POST:
                Mandato.objects.get(parlamentar=parlamentar).delete()
                parlamentar.delete()

            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form, 'legislatura_id': pk})


class MesaDiretoraForm(forms.Form):
    pass


class MesaDiretoraView(FormMixin, GenericView):
    template_name = "mesa_diretora/mesa_diretora.html"

    def get_success_url(self):
        return reverse('mesa_diretora')

    def get(self, request, *args, **kwargs):
        form = MesaDiretoraForm()

        mesa = SessaoLegislativa.objects.filter(
            legislatura=Legislatura.objects.last()).first(
        ).composicaomesa_set.all()

        cargos_ocupados = [m.cargo for m in mesa]
        cargos = CargoMesa.objects.all()
        cargos_vagos = list(set(cargos) - set(cargos_ocupados))

        parlamentares = Legislatura.objects.last().mandato_set.all()
        parlamentares_ocupados = [m.parlamentar for m in mesa]
        parlamentares_vagos = list(
            set(
                [p.parlamentar for p in parlamentares]) - set(
                parlamentares_ocupados))

        return self.render_to_response(
            {'form': form,
             'legislaturas': Legislatura.objects.all(
             ).order_by('-data_inicio'),
             'legislatura_selecionada': Legislatura.objects.last(),
             'sessoes': SessaoLegislativa.objects.filter(
                 legislatura=Legislatura.objects.last()),
             'sessao_selecionada': SessaoLegislativa.objects.filter(
                 legislatura=Legislatura.objects.last()).first(),
             'composicao_mesa': mesa,
             'parlamentares': parlamentares_vagos,
             'cargos_vagos': cargos_vagos
             })

    def post(self, request, *args, **kwargs):
        form = MesaDiretoraForm(request.POST)

        if 'Incluir' in request.POST:
            composicao = ComposicaoMesa()
            composicao.sessao_legislativa = SessaoLegislativa.objects.get(
                id=form.data['sessao'])
            composicao.parlamentar = Parlamentar.objects.get(
                id=form.data['parlamentar'])
            composicao.cargo = CargoMesa.objects.get(
                id=form.data['cargo'])
            composicao.save()
            return self.form_valid(form)
        elif 'Excluir' in request.POST:
            if 'composicao_mesa' in request.POST:
                ids = request.POST['composicao_mesa'].split(':')
                ComposicaoMesa.objects.filter(
                    sessao_legislativa=form.data['sessao'],
                    parlamentar=ids[0],
                    cargo=ids[1]
                ).delete()
            return self.form_valid(form)
        else:
            mesa = SessaoLegislativa.objects.filter(
                legislatura_id=int(form.data['legislatura'])).first(
            ).composicaomesa_set.all()

            cargos_ocupados = [m.cargo for m in mesa]
            cargos = CargoMesa.objects.all()
            cargos_vagos = list(set(cargos) - set(cargos_ocupados))

            parlamentares = Legislatura.objects.get(
                id=int(form.data['legislatura'])).mandato_set.all()
            parlamentares_ocupados = [m.parlamentar for m in mesa]
            parlamentares_vagos = list(
                set(
                    [p.parlamentar for p in parlamentares]) - set(
                    parlamentares_ocupados))

            return self.render_to_response(
                {'form': form,
                 'legislaturas': Legislatura.objects.all(
                 ).order_by('-data_inicio'),
                 'legislatura_selecionada': Legislatura.objects.get(
                     id=int(form.data['legislatura'])),
                 'sessoes': SessaoLegislativa.objects.filter(
                     legislatura_id=int(form.data['legislatura'])),
                 'sessao_selecionada': SessaoLegislativa.objects.get(
                     id=int(form.data['sessao'])),
                 'composicao_mesa': mesa,
                 'parlamentares': parlamentares_vagos,
                 'cargos_vagos': cargos_vagos
                 })
