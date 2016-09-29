from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, ListView

from sapl.comissoes.models import Participacao
from sapl.crud.base import (Crud, CrudBaseMixin, CrudCreateView,
                            CrudDeleteView, CrudDetailView, CrudListView,
                            CrudUpdateView, MasterDetailCrud, CrudAux,
                            RP_CHANGE)
from sapl.materia.models import Proposicao, Relatoria
from sapl.utils import permissao_tb_aux, permissoes_parlamentares

from .forms import (ComposicaoColigacaoForm, FiliacaoForm, FrenteForm,
                    LegislaturaForm, ParlamentarCreateForm, ParlamentarForm)
from .models import (CargoMesa, Coligacao, ComposicaoColigacao, ComposicaoMesa,
                     Dependente, Filiacao, Frente, Legislatura, Mandato,
                     NivelInstrucao, Parlamentar, Partido, SessaoLegislativa,
                     SituacaoMilitar, TipoAfastamento, TipoDependente)


class FrenteList(ListView):
    model = Frente
    paginate_by = 10
    template_name = 'parlamentares/frentes.html'

    def get_queryset(self):
        return Frente.objects.filter(parlamentares__in=[self.kwargs['pk']])

    def get_context_data(self, **kwargs):
        context = super(FrenteList, self).get_context_data(**kwargs)
        context['root_pk'] = self.kwargs['pk']
        context['object_list'] = self.get_queryset()
        return context


class FrenteCrud(CrudAux):
    model = Frente

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['nome', 'data_criacao', 'parlamentares']
        form_class = FrenteForm


class RelatoriaParlamentarCrud(MasterDetailCrud):
    model = Relatoria
    parent_field = 'parlamentar'

    class ListView(MasterDetailCrud.ListView):
        permission_required = permissoes_parlamentares()

    class CreateView(MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()


class ProposicaoParlamentarCrud(MasterDetailCrud):
    model = Proposicao
    parent_field = 'autor__parlamentar'
    help_path = ''

    class BaseMixin(CrudBaseMixin):
        list_field_names = ['tipo', 'descricao']

    class ListView(MasterDetailCrud.ListView):
        permission_required = permissoes_parlamentares()

        def get_context_data(self, **kwargs):
            context = super(ProposicaoParlamentarCrud.ListView, self
                            ).get_context_data(**kwargs)
            context['root_pk'] = self.kwargs['pk']
            return context

        def get_queryset(self):
            try:
                proposicoes = Proposicao.objects.filter(
                    autor__parlamentar_id=self.kwargs['pk'],
                    data_envio__isnull=False)
            except ObjectDoesNotExist:
                return []
            else:
                return proposicoes

    class CreateView(MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()


class ParticipacaoParlamentarCrud(MasterDetailCrud):
    model = Participacao
    parent_field = 'parlamentar'
    help_path = ''

    class ListView(MasterDetailCrud.ListView):
        ordering = ('-composicao__periodo')

        def get_rows(self, object_list):
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
            return ['Comissão', 'Cargo', 'Período']

    class CreateView(MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()


class CargoMesaCrud(Crud):
    model = CargoMesa
    help_path = 'cargo_mesa'

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class PartidoCrud(Crud):
    model = Partido
    help_path = 'partidos'

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class SessaoLegislativaCrud(Crud):
    model = SessaoLegislativa
    help_path = 'sessao_legislativa'

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class TipoDependenteCrud(Crud):
    model = TipoDependente
    help_path = 'nivel_instrucao'

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class NivelInstrucaoCrud(Crud):
    model = NivelInstrucao
    help_path = 'tipo_dependente'

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class TipoAfastamentoCrud(Crud):
    model = TipoAfastamento
    help_path = 'tipo_afastamento'

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class TipoMilitarCrud(Crud):
    model = SituacaoMilitar
    help_path = 'tipo_situa_militar'

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class DependenteCrud(MasterDetailCrud):
    model = Dependente
    parent_field = 'parlamentar'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()

    class ListView(MasterDetailCrud.ListView):
        permission_required = permissoes_parlamentares()

    class DetailView(MasterDetailCrud.DetailView):
        permission_required = permissoes_parlamentares()


class MandatoCrud(MasterDetailCrud):
    model = Mandato
    parent_field = 'parlamentar'
    help_path = ''

    class ListView(MasterDetailCrud.ListView):
        ordering = ('-legislatura__numero')

    class CreateView(MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()


class ColigacaoCrud(Crud):
    model = Coligacao
    help_path = 'tabelas_auxiliares#coligacao'

    class ListView(CrudListView):
        ordering = ('-numero_votos', 'nome')

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class ComposicaoColigacaoCrud(MasterDetailCrud):
    model = ComposicaoColigacao
    parent_field = 'coligacao'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ComposicaoColigacaoForm

        def get_initial(self):
            id = self.kwargs['pk']
            return {'coligacao_id': id}

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ComposicaoColigacaoForm

        def get_initial(self):
            id = self.kwargs['pk']
            return {'coligacao_id': id}

    class ListView(MasterDetailCrud.ListView):
        ordering = '-partido__sigla'

    class BaseMixin(MasterDetailCrud.BaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class LegislaturaCrud(Crud):
    model = Legislatura
    help_path = 'tabelas_auxiliares#legislatura'

    class CreateView(CrudCreateView):
        form_class = LegislaturaForm

    class UpdateView(CrudUpdateView):
        form_class = LegislaturaForm

    class BaseMixin(CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class FiliacaoCrud(MasterDetailCrud):
    model = Filiacao
    parent_field = 'parlamentar'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = FiliacaoForm
        permission_required = permissoes_parlamentares()

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = FiliacaoForm
        permission_required = permissoes_parlamentares()

    class DeleteView(MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()

    class ListView(MasterDetailCrud.ListView):
        ordering = '-data'


class ParlamentarCrud(Crud):
    model = Parlamentar

    class BaseMixin(Crud.BaseMixin):
        form_class = ParlamentarCreateForm
        list_field_names = [
            'avatar_html', 'nome_parlamentar', 'filiacao_atual', 'ativo']

    class DetailView(Crud.DetailView):
        permission_required = []

        def get_template_names(self):
            return ['crud/detail.html']\
                if self.request.user.has_perm(self.permission(RP_CHANGE))\
                else ['parlamentares/parlamentar_perfil_publico.html']

    class UpdateView(Crud.UpdateView):
        form_class = ParlamentarForm

    class CreateView(Crud.CreateView):

        @property
        def layout_key(self):
            return 'ParlamentarCreate'

    class ListView(Crud.ListView):
        permission_required = []
        template_name = "parlamentares/parlamentares_list.html"
        paginate_by = None

        def take_legislatura_id(self):
            try:
                return int(self.request.GET['periodo'])
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


def check_permission_mesa(request):
    lista_permissoes = []
    cts = ContentType.objects.filter(app_label='parlamentares')
    cts = cts.filter(model__icontains='mesa')
    perms = list(Permission.objects.filter(content_type__in=cts))
    for p in perms:
        lista_permissoes.append('parlamentares.' + p.codename)

    return request.user.has_perms(set(lista_permissoes))


class MesaDiretoraView(FormView):
    template_name = "mesa_diretora/mesa_diretora.html"
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
                not SessaoLegislativa.objects.all()):
            return self.validation(request)

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
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-numero'),
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
        if 'Incluir' in request.POST and check_permission_mesa(request):

            if (not Legislatura.objects.all() or
                    not SessaoLegislativa.objects.all()):
                return self.validation(request)

            composicao = ComposicaoMesa()
            composicao.sessao_legislativa = SessaoLegislativa.objects.get(
                id=int(request.POST['sessao']))
            composicao.parlamentar = Parlamentar.objects.get(
                id=int(request.POST['parlamentar']))
            composicao.cargo = CargoMesa.objects.get(
                id=int(request.POST['cargo']))
            composicao.save()

            return redirect('sapl.parlamentares:mesa_diretora')

        elif 'Excluir' in request.POST and check_permission_mesa(request):

            if (not Legislatura.objects.all() or
                    not SessaoLegislativa.objects.all()):
                return self.validation(request)

            if 'composicao_mesa' in request.POST:
                ids = request.POST['composicao_mesa'].split(':')
                composicao = ComposicaoMesa.objects.get(
                    sessao_legislativa_id=int(request.POST['sessao']),
                    parlamentar_id=int(ids[0]),
                    cargo_id=int(ids[1])
                )
                composicao.delete()
            return redirect('sapl.parlamentares:mesa_diretora')
        else:
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
            return self.render_to_response(
                {'legislaturas': Legislatura.objects.all(
                ).order_by('-numero'),
                    'legislatura_selecionada': Legislatura.objects.get(
                    id=int(request.POST['legislatura'])),
                    'sessoes': SessaoLegislativa.objects.filter(
                    legislatura_id=int(request.POST['legislatura'])),
                    'sessao_selecionada': SessaoLegislativa.objects.get(
                    id=int(request.POST['sessao'])),
                    'composicao_mesa': mesa,
                    'parlamentares': parlamentares_vagos,
                    'cargos_vagos': cargos_vagos
                })
