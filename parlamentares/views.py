from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

import crud.base
import crud.masterdetail
from crud.base import Crud
from crud.masterdetail import MasterDetailCrud

from .forms import FiliacaoForm, ParlamentarCreateForm, ParlamentarForm
from .models import (CargoMesa, Coligacao, ComposicaoMesa, Dependente,
                     Filiacao, Legislatura, Mandato, NivelInstrucao,
                     Parlamentar, Partido, SessaoLegislativa, SituacaoMilitar,
                     TipoAfastamento, TipoDependente)

CargoMesaCrud = Crud.build(CargoMesa, 'cargo_mesa')
LegislaturaCrud = Crud.build(Legislatura, 'tabelas_auxiliares#legislatura')
ColigacaoCrud = Crud.build(Coligacao, 'coligacao')
PartidoCrud = Crud.build(Partido, 'partidos')
SessaoLegislativaCrud = Crud.build(SessaoLegislativa, 'sessao_legislativa')
TipoDependenteCrud = Crud.build(TipoDependente, 'tipo_dependente')
NivelInstrucaoCrud = Crud.build(NivelInstrucao, 'nivel_instrucao')
TipoAfastamentoCrud = Crud.build(TipoAfastamento, 'tipo_afastamento')
TipoMilitarCrud = Crud.build(SituacaoMilitar, 'tipo_situa_militar')

DependenteCrud = MasterDetailCrud.build(Dependente, 'parlamentar', '')
MandatoCrud = MasterDetailCrud.build(Mandato, 'parlamentar', '')


class FiliacaoCrud(MasterDetailCrud):
    model = Filiacao
    parent_field = 'parlamentar'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = FiliacaoForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = FiliacaoForm

    class ListView(MasterDetailCrud.ListView):
        ordering = '-data'


class ParlamentarCrud(Crud):
    model = Parlamentar
    help_path = ''

    class UpdateView(crud.base.CrudUpdateView):
        form_class = ParlamentarForm

    class CreateView(crud.base.CrudCreateView):
        form_class = ParlamentarCreateForm

        @property
        def layout_key(self):
            return 'ParlamentarCreate'

    class ListView(crud.base.CrudListView):
        template_name = "parlamentares/parlamentares_list.html"
        paginate_by = None

        def take_legislatura_id(self):
            legislaturas = Legislatura.objects.all().order_by(
                '-data_inicio', '-data_fim')

            try:
                legislatura_id = int(self.request.GET['periodo'])
            except MultiValueDictKeyError:
                legislatura_id = legislaturas.first().id

            return legislatura_id

        def get_queryset(self):
            mandatos = Mandato.objects.filter(
                legislatura_id=self.take_legislatura_id())
            return mandatos

        def get_rows(self, object_list):
            parlamentares = []
            for m in object_list:
                ultima_filiacao = m.parlamentar.filiacao_set.\
                                    order_by('-data').first()
                if ultima_filiacao and not ultima_filiacao.data_desfiliacao:
                    partido = ultima_filiacao.partido.sigla
                else:
                    partido = _('Sem Partido')

                parlamentar = [
                    (m.parlamentar.nome_parlamentar, m.parlamentar.id),
                    (partido, None),
                    ('Sim' if m.parlamentar.ativo else 'Não', None)
                ]
                parlamentares.append(parlamentar)
            return parlamentares

        def get_headers(self):
            return ['Parlamentar', 'Partido', 'Ativo?']

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


class MesaDiretoraView(FormView):
    template_name = "mesa_diretora/mesa_diretora.html"
    success_url = reverse_lazy('parlamentares:mesa_diretora')

    # Essa função avisa quando se pode compor uma Mesa Legislativa)
    def validation(self, request):
        mensagem = _("Não há nenhuma Sessão Legislativa cadastrada. \
        Só é possível compor uma Mesa Diretora quando há uma Sessão \
        Legislativa cadastrada.")
        messages.add_message(request, messages.INFO, mensagem)

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-data_inicio'),
                'legislatura_selecionada': Legislatura.objects.last(),
                'cargos_vagos': CargoMesa.objects.all()})

    def get(self, request, *args, **kwargs):

        if (not Legislatura.objects.all() or
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
        if 'Incluir' in request.POST:

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

            return redirect('parlamentares:mesa_diretora')

        elif 'Excluir' in request.POST:

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
            return redirect('parlamentares:mesa_diretora')
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
