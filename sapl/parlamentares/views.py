from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from sapl.comissoes.models import Participacao
from sapl.crud.base import (Crud, CrudBaseMixin, CrudCreateView,
                            CrudDeleteView, CrudDetailView, CrudListView,
                            CrudUpdateView)
from sapl.crud.masterdetail import MasterDetailCrud
from sapl.utils import permissao_tb_aux, permissoes_parlamentares

from .forms import (ComposicaoColigacaoForm, FiliacaoForm, LegislaturaForm,
                    ParlamentarCreateForm, ParlamentarForm)
from .models import (CargoMesa, Coligacao, ComposicaoColigacao, ComposicaoMesa,
                     Dependente, Filiacao, Legislatura, Mandato,
                     NivelInstrucao, Parlamentar, Partido, SessaoLegislativa,
                     SituacaoMilitar, TipoAfastamento, TipoDependente)


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
                        (p.composicao.comissao.nome, p.composicao.comissao.pk),
                        (p.cargo.nome, None),
                        (p.composicao.periodo, None)
                    ]
                    comissoes.append(comissao)
            return comissoes

        def get_headers(self):
            return ['Comissão', 'Cargo', 'Período']

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()


class CargoMesaCrud(Crud):
    model = CargoMesa
    help_path = 'cargo_mesa'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class PartidoCrud(Crud):
    model = Partido
    help_path = 'partidos'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class SessaoLegislativaCrud(Crud):
    model = SessaoLegislativa
    help_path = 'sessao_legislativa'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class TipoDependenteCrud(Crud):
    model = TipoDependente
    help_path = 'nivel_instrucao'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class NivelInstrucaoCrud(Crud):
    model = NivelInstrucao
    help_path = 'tipo_dependente'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class TipoAfastamentoCrud(Crud):
    model = TipoAfastamento
    help_path = 'tipo_afastamento'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class TipoMilitarCrud(Crud):
    model = SituacaoMilitar
    help_path = 'tipo_situa_militar'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class DependenteCrud(MasterDetailCrud):
    model = Dependente
    parent_field = 'parlamentar'
    help_path = ''

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()

    class ListView(PermissionRequiredMixin, MasterDetailCrud.ListView):
        permission_required = permissoes_parlamentares()

    class DetailView(PermissionRequiredMixin, MasterDetailCrud.DetailView):
        permission_required = permissoes_parlamentares()


class MandatoCrud(MasterDetailCrud):
    model = Mandato
    parent_field = 'parlamentar'
    help_path = ''

    class ListView(MasterDetailCrud.ListView):
        ordering = ('-legislatura__data_inicio')

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        permission_required = permissoes_parlamentares()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        permission_required = permissoes_parlamentares()

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()


class ColigacaoCrud(Crud):
    model = Coligacao
    help_path = 'tabelas_auxiliares#coligacao'

    class ListView(CrudListView):
        ordering = ('-legislatura__data_inicio', 'nome')

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
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

    class BaseMixin(PermissionRequiredMixin, MasterDetailCrud.BaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class LegislaturaCrud(Crud):
    model = Legislatura
    help_path = 'tabelas_auxiliares#legislatura'

    class CreateView(CrudCreateView):
        form_class = LegislaturaForm

    class UpdateView(CrudUpdateView):
        form_class = LegislaturaForm

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class FiliacaoCrud(MasterDetailCrud):
    model = Filiacao
    parent_field = 'parlamentar'
    help_path = ''

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = FiliacaoForm
        permission_required = permissoes_parlamentares()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = FiliacaoForm
        permission_required = permissoes_parlamentares()

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_parlamentares()

    class ListView(MasterDetailCrud.ListView):
        ordering = '-data'


def get_parlamentar_permissions():
        lista_permissoes = []
        cts = ContentType.objects.filter(app_label='parlamentares')
        perms_parlamentares = list(Permission.objects.filter(
            content_type__in=cts))
        for p in perms_parlamentares:
            lista_permissoes.append('parlamentares.' + p.codename)
        return set(lista_permissoes)


class ParlamentarCrud(Crud):
    model = Parlamentar
    help_path = ''

    class DetailView(CrudDetailView):
        def get_template_names(self):
            usuario = self.request.user
            lista_permissoes = get_parlamentar_permissions()

            if usuario.has_perms(lista_permissoes):
                return ['crud/detail.html']

            else:
                return ['parlamentares/parlamentar_perfil_publico.html']

    class UpdateView(PermissionRequiredMixin, CrudUpdateView):
        form_class = ParlamentarForm
        permission_required = permissoes_parlamentares()

    class CreateView(PermissionRequiredMixin, CrudCreateView):
        form_class = ParlamentarCreateForm
        permission_required = permissoes_parlamentares()

        @property
        def layout_key(self):
            return 'ParlamentarCreate'

    class DeleteView(PermissionRequiredMixin, CrudDeleteView):
        form_class = ParlamentarCreateForm
        permission_required = permissoes_parlamentares()

    class ListView(CrudListView):
        template_name = "parlamentares/parlamentares_list.html"
        paginate_by = None

        def take_legislatura_id(self):
            legislaturas = Legislatura.objects.all().order_by(
                '-data_inicio', '-data_fim')

            if legislaturas:
                try:
                    legislatura_id = int(self.request.GET['periodo'])
                except MultiValueDictKeyError:
                    legislatura_id = legislaturas.first().id
                return legislatura_id
            else:
                return 0

        def get_queryset(self):
            if self.take_legislatura_id() != 0:
                mandatos = Mandato.objects.filter(
                    legislatura_id=self.take_legislatura_id())
                return mandatos
            return []

        def get_rows(self, object_list):
            parlamentares = []
            for m in object_list:
                ultima_filiacao = m.parlamentar.filiacao_set.order_by(
                    '-data').first()
                if ultima_filiacao and not ultima_filiacao.data_desfiliacao:
                    partido = ultima_filiacao.partido.sigla
                else:
                    partido = _('Sem Partido')

                parlamentar = [
                    ("<img src=" + m.parlamentar.fotografia.url + " \
                     height='42' width='42' />" if m.parlamentar.fotografia
                     else '', ''),
                    (m.parlamentar.nome_parlamentar, m.parlamentar.id),
                    (partido, None),
                    ('Sim' if m.parlamentar.ativo else 'Não', None)
                ]
                parlamentares.append(parlamentar)
            return parlamentares

        def get_headers(self):
            return ['', 'Parlamentar', 'Partido', 'Ativo?']

        def get_context_data(self, **kwargs):
            context = super(ParlamentarCrud.ListView, self
                            ).get_context_data(**kwargs)
            context.setdefault('title', self.verbose_name_plural)

            # Adiciona legislatura para filtrar parlamentares
            legislaturas = Legislatura.objects.all().order_by(
                '-data_inicio', '-data_fim')
            context['legislaturas'] = legislaturas
            context['legislatura_id'] = self.take_legislatura_id()
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
            ).order_by('-data_inicio'),
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
                ).order_by('-data_inicio'),
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
