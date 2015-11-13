from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Fieldset, Layout, Submit
from django import forms
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin
from vanilla import GenericView

from parlamentares.models import Filiacao, Parlamentar
from sapl.crud import build_crud

from .models import (CargoComissao, Comissao, Composicao, Participacao,
                     Periodo, TipoComissao)

cargo_crud = build_crud(
    CargoComissao, 'cargo_comissao', [

        [_('Período de composição de Comissão'),
         [('nome', 10), ('unico', 2)]],
    ])

periodo_composicao_crud = build_crud(
    Periodo, 'periodo_composicao_comissao', [

        [_('Cargo de Comissão'),
         [('data_inicio', 6), ('data_fim', 6)]],
    ])

tipo_comissao_crud = build_crud(
    TipoComissao, 'tipo_comissao', [

        [_('Tipo Comissão'),
         [('nome', 9), ('sigla', 3)],
            [('dispositivo_regimental', 9), ('natureza', 3)]],
    ])

comissao_crud = build_crud(
    Comissao, 'modulo_comissoes', [

        [_('Dados Básicos'),
         [('nome', 9), ('sigla', 3)],
         [('tipo', 3),
          ('data_criacao', 3),
          ('unidade_deliberativa', 3),
          ('data_extincao', 3)]],

        [_('Dados Complementares'),
         [('local_reuniao', 4),
          ('agenda_reuniao', 4),
          ('telefone_reuniao', 4)],
         [('endereco_secretaria', 4),
          ('telefone_secretaria', 4),
          ('fax_secretaria', 4)],
         [('secretario', 4), ('email', 8)],
         [('finalidade', 12)]],

        [_('Temporária'),
         [('apelido_temp', 8),
          ('data_instalacao_temp', 4)],
         [('data_final_prevista_temp', 4),
          ('data_prorrogada_temp', 4),
          ('data_fim_comissao', 4)]],
    ])


class ComposicaoForm(forms.Form):
    periodo = forms.CharField()


class ComposicaoView(FormMixin, GenericView):
    template_name = 'comissoes/composicao.html'

    def get(self, request, *args, **kwargs):
        form = ComposicaoForm()

        composicoes = Composicao.objects.filter(
            comissao_id=self.kwargs['pk']).order_by('-periodo')
        participacoes = Participacao.objects.all()

        return self.render_to_response({
            'participacoes': participacoes,
            'composicoes': composicoes,
            'composicao_id': composicoes.first().id,
            'form': form,
            'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        form = ComposicaoForm(request.POST)

        composicoes = Composicao.objects.filter(
            comissao_id=self.kwargs['pk']).order_by('-periodo')
        participacoes = Participacao.objects.all()

        return self.render_to_response({
            'participacoes': participacoes,
            'composicoes': composicoes,
            'composicao_id': int(form.data['periodo']),
            'form': form,
            'pk': self.kwargs['pk']})


class MateriasView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/materias.html'


class ReunioesView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/reunioes.html'

PARLAMENTARES_CHOICES = [('', '---------')] + [
        (p.parlamentar.id,
         p.parlamentar.nome_parlamentar + ' / ' + p.partido.sigla)
        for p in Filiacao.objects.filter(
            data_desfiliacao__isnull=True, parlamentar__ativo=True).order_by(
            'parlamentar__nome_parlamentar')]

class ParticipacaoCadastroForm(ModelForm):

    YES_OR_NO = (
        (True, 'Sim'),
        (False, 'Não')
    )

    parlamentar_id = forms.ChoiceField(required=True,
                                       label='Parlamentar',
                                       choices=PARLAMENTARES_CHOICES,
                                       widget=forms.Select(
                                           attrs={'class': 'selector'}))

    titular = forms.BooleanField(
        widget=forms.RadioSelect(choices=YES_OR_NO), required=True)

    data_designacao = forms.DateField(label=u'Data Designação',
                                      input_formats=['%d/%m/%Y'],
                                      required=True,
                                      widget=forms.DateInput(
                                          format='%d/%m/%Y'))

    data_desligamento = forms.DateField(label=u'Data Desligamento',
                                        input_formats=['%d/%m/%Y'],
                                        required=False,
                                        widget=forms.DateInput(
                                            format='%d/%m/%Y'))

    class Meta:
        model = Participacao
        fields = ['parlamentar_id',
                  'cargo',
                  'titular',
                  'data_designacao',
                  'data_desligamento',
                  'motivo_desligamento',
                  'observacao']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Formulário de Cadastro',
                'parlamentar_id',
                'cargo',
                'titular',
                'data_designacao',
                'data_desligamento',
                'motivo_desligamento',
                'observacao'
            ),
            ButtonHolder(
                Submit('submit', 'Salvar',
                       css_class='button primary')
            )
        )
        super(ParticipacaoCadastroForm, self).__init__(*args, **kwargs)


class ComissaoParlamentarIncluirView(FormMixin, GenericView):
    template_name = "comissoes/comissao_parlamentar.html"

    def get(self, request, *args, **kwargs):
        form = ParticipacaoCadastroForm()
        return self.render_to_response({'form': form,
                                        'composicao_id': self.kwargs['id']})

    def post(self, request, *args, **kwargs):
        composicao = Composicao.objects.get(id=self.kwargs['id'])
        form = ParticipacaoCadastroForm(request.POST)

        if form.is_valid():
            cargo = form.cleaned_data['cargo']
            if cargo.nome == 'Presidente':
                for p in Participacao.objects.filter(composicao=composicao):
                    if p.cargo.nome == 'Presidente':
                        return self.render_to_response(
                            {'form': form,
                             'composicao_id': self.kwargs['id'],
                             'error': 'Esse cargo já está sendo ocupado!'})
                    else:
                        # Pensar em forma melhor para não duplicar código
                        participacao = form.save(commit=False)
                        parlamentar = Parlamentar.objects.get(
                            id=int(form.cleaned_data['parlamentar_id']))

                        participacao.composicao = composicao
                        participacao.parlamentar = parlamentar

                        participacao.save()
            else:
                participacao = form.save(commit=False)
                parlamentar = Parlamentar.objects.get(
                    id=int(form.cleaned_data['parlamentar_id']))

                participacao.composicao = composicao
                participacao.parlamentar = parlamentar

                participacao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'composicao_id': self.kwargs['id']})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('comissao:composicao', kwargs={'pk': pk})

class ComissaoParlamentarEditView(FormMixin, GenericView):
    template_name = "comissoes/comissao_parlamentar_edit.html"

    def get(self, request, *args, **kwargs):
        participacao_id = kwargs['id']
        participacao = Participacao.objects.get(id = participacao_id)        
        form = ParticipacaoCadastroForm(initial={'parlamentar_id': participacao.parlamentar.id}, instance=participacao)
        print(form)
        return self.render_to_response({'form': form,
                                        'composicao_id': self.kwargs['id']})    
