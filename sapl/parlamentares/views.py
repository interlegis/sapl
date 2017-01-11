
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from sapl.comissoes.models import Participacao
from sapl.crud.base import (RP_CHANGE, RP_DETAIL, RP_LIST, Crud, CrudAux,
                            CrudBaseForListAndDetailExternalAppView,
                            MasterDetailCrud)
from sapl.materia.models import Proposicao, Relatoria
from sapl.parlamentares.apps import AppConfig

from .forms import (FiliacaoForm, LegislaturaCreateForm, LegislaturaUpdateForm,
                    ParlamentarCreateForm, ParlamentarForm)
from .models import (CargoMesa, Coligacao, ComposicaoColigacao, ComposicaoMesa,
                     Dependente, Filiacao, Frente, Legislatura, Mandato,
                     NivelInstrucao, Parlamentar, Partido, SessaoLegislativa,
                     SituacaoMilitar, TipoAfastamento, TipoDependente)

CargoMesaCrud = CrudAux.build(CargoMesa, 'cargo_mesa')
PartidoCrud = CrudAux.build(Partido, 'partidos')
SessaoLegislativaCrud = CrudAux.build(SessaoLegislativa, 'sessao_legislativa')
TipoDependenteCrud = CrudAux.build(TipoDependente, 'tipo_dependente')
NivelInstrucaoCrud = CrudAux.build(NivelInstrucao, 'nivel_instrucao')
TipoAfastamentoCrud = CrudAux.build(TipoAfastamento, 'tipo_afastamento')
TipoMilitarCrud = CrudAux.build(SituacaoMilitar, 'tipo_situa_militar')

FrenteCrud = CrudAux.build(Frente, 'tipo_situa_militar', list_field_names=[
    'nome', 'data_criacao', 'parlamentares'])

DependenteCrud = MasterDetailCrud.build(
    Dependente, 'parlamentar', 'dependente')


class FrenteList(MasterDetailCrud):
    model = Frente
    is_m2m = True
    parent_field = 'parlamentares'
    CreateView, UpdateView, DeleteView = None, None, None

    class BaseMixin(Crud.PublicMixin, MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'data_criacao']

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)


class RelatoriaParlamentarCrud(CrudBaseForListAndDetailExternalAppView):
    model = Relatoria
    parent_field = 'parlamentar'
    help_path = 'relatoria_parlamentar'
    namespace = AppConfig.name

    class BaseMixin(CrudBaseForListAndDetailExternalAppView.BaseMixin):

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)


class ProposicaoParlamentarCrud(CrudBaseForListAndDetailExternalAppView):
    model = Proposicao
    list_field_names = ['tipo', 'descricao']
    parent_field = 'autor__parlamentar_set'
    namespace = AppConfig.name

    class BaseMixin(CrudBaseForListAndDetailExternalAppView.BaseMixin):

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)

    class ListView(CrudBaseForListAndDetailExternalAppView.ListView):

        def get_queryset(self):
            return super().get_queryset().filter(
                data_envio__isnull=False,
                data_recebimento__isnull=False)

    class DetailView(CrudBaseForListAndDetailExternalAppView.DetailView):

        @property
        def extras_url(self):

            if self.object.texto_articulado.exists():
                ta = self.object.texto_articulado.first()
                yield (str(reverse_lazy(
                    'sapl.compilacao:ta_text',
                    kwargs={'ta_id': ta.pk})) + '?back_type=history',
                    'btn-success',
                    _('Texto Eletrônico'))


class ParticipacaoParlamentarCrud(CrudBaseForListAndDetailExternalAppView):
    model = Participacao
    parent_field = 'parlamentar'
    namespace = AppConfig.name
    list_field_names = ['composicao__comissao__nome', 'cargo__nome', (
        'composicao__periodo__data_inicio', 'composicao__periodo__data_fim')]

    class BaseMixin(CrudBaseForListAndDetailExternalAppView.BaseMixin):

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)

    class ListView(CrudBaseForListAndDetailExternalAppView.ListView):
        ordering = ('-composicao__periodo')

        def get_rows(self, object_list):
            """
            FIXME:
                Este metodo não será necessário quando get_rows for refatorada
            """

            comissoes = []
            for p in object_list:
                if p.cargo.nome != 'Relator':
                    comissao = [
                        (p.composicao.comissao.nome, reverse(
                            'sapl.comissoes:comissao_detail', kwargs={
                                'pk': p.composicao.comissao.pk})),
                        (p.cargo.nome, None),
                        (p.composicao.periodo.data_inicio.strftime(
                         "%d/%m/%Y") + ' a ' +
                         p.composicao.periodo.data_fim.strftime("%d/%m/%Y"),
                         None)
                    ]
                    comissoes.append(comissao)
            return comissoes

        def get_headers(self):
            return [_('Comissão'), _('Cargo'), _('Período de participação'), ]


class ColigacaoCrud(CrudAux):
    model = Coligacao
    help_path = 'tabelas_auxiliares#coligacao'

    class ListView(CrudAux.ListView):
        ordering = ('-numero_votos', 'nome')

    class BaseMixin(CrudAux.BaseMixin):
        subnav_template_name = 'parlamentares/subnav_coligacao.yaml'


class MandatoCrud(MasterDetailCrud):
    model = Mandato
    parent_field = 'parlamentar'
    public = [RP_DETAIL, RP_LIST]
    list_field_names = ['legislatura',
                        'votos_recebidos',
                        'coligacao',
                        'coligacao__numero_votos']

    class ListView(MasterDetailCrud.ListView):
        ordering = ('-legislatura__numero')


class ComposicaoColigacaoCrud(MasterDetailCrud):
    model = ComposicaoColigacao
    parent_field = 'coligacao'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data()
            context['subnav_template_name'] = \
                'parlamentares/subnav_coligacao.yaml'
            return context

    class ListView(MasterDetailCrud.ListView):
        ordering = '-partido__sigla'


class LegislaturaCrud(CrudAux):
    model = Legislatura
    help_path = 'tabelas_auxiliares#legislatura'

    class CreateView(CrudAux.CreateView):
        form_class = LegislaturaCreateForm

        def get_initial(self):
            try:
                ultima_legislatura = Legislatura.objects.latest('numero')
                numero = ultima_legislatura.numero + 1
            except Legislatura.DoesNotExist:
                numero = 1
            return {'numero': numero}

    class UpdateView(CrudAux.UpdateView):
        form_class = LegislaturaUpdateForm


class FiliacaoCrud(MasterDetailCrud):
    model = Filiacao
    parent_field = 'parlamentar'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        ordering = '-data'

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = FiliacaoForm

    class CreateView(MasterDetailCrud.CreateView):
        form_class = FiliacaoForm


class ParlamentarCrud(Crud):
    model = Parlamentar
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        ordered_list = False
        list_field_names = [
            'avatar_html', 'nome_parlamentar', 'filiacao_atual', 'ativo']

    class DetailView(Crud.DetailView):

        def get_template_names(self):
            return ['crud/detail.html']\
                if self.request.user.has_perm(self.permission(RP_CHANGE))\
                else ['parlamentares/parlamentar_perfil_publico.html']

    class UpdateView(Crud.UpdateView):
        form_class = ParlamentarForm

    class CreateView(Crud.CreateView):
        form_class = ParlamentarCreateForm

        @property
        def layout_key(self):
            return 'ParlamentarCreate'

        def form_valid(self, form):
            '''
            Reimplementa form_valid devido ao save de ParlamentarCreateForm
            ser específico, sendo necessário isolar padrão do crud que aciona
            form.save(commit=False) para registrar dados de auditoria se
            o model implementá-los, bem como de container se também implement.
            '''
            return super(Crud.CreateView, self).form_valid(form)

    class ListView(Crud.ListView):
        template_name = "parlamentares/parlamentares_list.html"
        paginate_by = None

        def take_legislatura_id(self):
            try:
                return int(self.request.GET['pk'])
            except:
                for l in Legislatura.objects.all():
                    if l.atual():
                        return l.id
                return 0

        def get_queryset(self):
            queryset = super().get_queryset()

            legislatura_id = self.take_legislatura_id()
            if legislatura_id != 0:
                queryset = queryset.filter(
                    mandato__legislatura_id=legislatura_id)
            return queryset

        def get_headers(self):
            return ['', _('Parlamentar'), _('Partido'), _('Ativo?')]

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            # Adiciona legislatura para filtrar parlamentares
            legislaturas = Legislatura.objects.all().order_by('-numero')
            context['legislaturas'] = legislaturas
            context['legislatura_id'] = self.take_legislatura_id()

            # Tira Link do avatar_html e coloca no nome
            for row in context['rows']:
                row[1] = (row[1][0], row[0][1])
                row[0] = (row[0][0], None)
            return context


class MesaDiretoraView(FormView):
    template_name = 'parlamentares/composicaomesa_form.html'
    success_url = reverse_lazy('sapl.parlamentares:mesa_diretora')

    # Essa função avisa quando se pode compor uma Mesa Legislativa
    def validation(self, request):
        mensagem = _('Não há nenhuma Sessão Legislativa cadastrada. ' +
                     'Só é possível compor uma Mesa Diretora quando ' +
                     'há uma Sessão Legislativa cadastrada.')
        messages.add_message(request, messages.INFO, mensagem)

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-numero'),
                'legislatura_selecionada': Legislatura.objects.last(),
                'cargos_vagos': CargoMesa.objects.all()})

    def get(self, request, *args, **kwargs):

        if (not Legislatura.objects.exists() or
                not SessaoLegislativa.objects.exists()):
            return self.validation(request)

        sessao = SessaoLegislativa.objects.filter(
            legislatura=Legislatura.objects.first()).first(
        )

        if sessao:
            mesa = sessao.composicaomesa_set.all()
        else:
            mesa = []

        cargos_ocupados = [m.cargo for m in mesa]
        cargos = CargoMesa.objects.all()
        cargos_vagos = list(set(cargos) - set(cargos_ocupados))

        parlamentares = Legislatura.objects.first().mandato_set.all()
        parlamentares_ocupados = [m.parlamentar for m in mesa]
        parlamentares_vagos = list(
            set(
                [p.parlamentar for p in parlamentares]) - set(
                parlamentares_ocupados))

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-numero'),
                'legislatura_selecionada': Legislatura.objects.first(),
                'sessoes': SessaoLegislativa.objects.filter(
                legislatura=Legislatura.objects.first()),
                'sessao_selecionada': SessaoLegislativa.objects.filter(
                legislatura=Legislatura.objects.first()).first(),
                'composicao_mesa': mesa,
                'parlamentares': parlamentares_vagos,
                'cargos_vagos': cargos_vagos
            })

    def existe_membro_mesa(self, sessao_plenaria, cargo):
        return ComposicaoMesa.objects.filter(
            sessao_legislativa_id=sessao_plenaria.id,
            #parlamentar_id = integrante.parlamentar_id,
            cargo_id = cargo.id
            ).exists()

    def post(self, request, *args, **kwargs):

        if (not Legislatura.objects.exists() or
                not SessaoLegislativa.objects.exists()):
            return self.validation(request)

        if 'Incluir' in request.POST and request.user.has_perm(
                '%s.add_%s' % (
                    AppConfig.label, ComposicaoMesa._meta.model_name)):

            composicao = ComposicaoMesa()

            try:
                composicao.sessao_legislativa = SessaoLegislativa.objects.get(
                    id=int(request.POST['sessao']))
            except MultiValueDictKeyError:
                messages.error(request, _(
                    'Nenhuma sessão foi inserida!'))
                return self.get(request)

            try:
                composicao.parlamentar = Parlamentar.objects.get(
                    id=int(request.POST['parlamentar']))
            except MultiValueDictKeyError:
                messages.error(request, _(
                    'Nenhum parlamentar foi inserido!'))
                return self.get(request)

            try:
                composicao.cargo = CargoMesa.objects.get(
                    id=int(request.POST['cargo']))
                if self.existe_membro_mesa(composicao.sessao_legislativa,
                                           composicao.cargo):
                    messages.error(request, _('Parlamentar já inserido!'))
                    return self.get(request)

                composicao.save()
            except MultiValueDictKeyError:
                messages.error(request, _(
                    'Nenhum cargo foi inserido!'))
                return self.get(request)

            messages.success(request, _(
                'Parlamentar adicionado com sucesso!'))

        elif 'Excluir' in request.POST and request.user.has_perm(
                '%s.delete_%s' % (
                    AppConfig.label, ComposicaoMesa._meta.model_name)):

            if 'composicao_mesa' in request.POST:
                ids = request.POST['composicao_mesa'].split(':')
                composicao = ComposicaoMesa.objects.get(
                    sessao_legislativa_id=int(request.POST['sessao']),
                    parlamentar_id=int(ids[0]),
                    cargo_id=int(ids[1])
                )
                composicao.delete()
                messages.success(request, _(
                    'Parlamentar excluido com sucesso!'))
            else:
                messages.error(request, _(
                    'Selecione um parlamentar para ser excluido!'))

        mesa = ComposicaoMesa.objects.filter(
            sessao_legislativa=request.POST['sessao'])

        cargos_ocupados = [m.cargo for m in mesa]
        cargos = CargoMesa.objects.all()
        cargos_vagos = list(set(cargos) - set(cargos_ocupados))

        parlamentares = Legislatura.objects.get(
            id=int(request.POST['legislatura'])).mandato_set.all()
        parlamentares_ocupados = [m.parlamentar for m in mesa]
        parlamentares_vagos = list(
            set(
                [p.parlamentar for p in parlamentares]) - set(
                parlamentares_ocupados))

        sessao_sel = SessaoLegislativa.objects.get(
            id=int(request.POST['sessao']))

        if str(sessao_sel.legislatura_id) != request.POST['legislatura']:
            sessao_sel = SessaoLegislativa.objects.filter(
                legislatura=Legislatura.objects.first()).first()

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-numero'),
                'legislatura_selecionada': Legislatura.objects.get(
                id=int(request.POST['legislatura'])),
                'sessoes': SessaoLegislativa.objects.filter(
                legislatura_id=int(request.POST['legislatura'])),
                'sessao_selecionada': sessao_sel,
                'composicao_mesa': mesa,
                'parlamentares': parlamentares_vagos,
                'cargos_vagos': cargos_vagos
            })
