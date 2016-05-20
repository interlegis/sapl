from datetime import datetime
from random import choice
from string import ascii_letters, digits

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, TemplateView, UpdateView
from django_filters.views import FilterView

import crispy_layout_mixin
import crud.base
import crud.masterdetail
import sapl
from base.models import CasaLegislativa
from compilacao.views import IntegracaoTaView
from crispy_layout_mixin import form_actions
from crud.base import Crud, make_pagination
from crud.masterdetail import MasterDetailCrud
from norma.models import LegislacaoCitada
from sapl.utils import get_base_url

from .forms import (AcompanhamentoMateriaForm, AnexadaForm, AutoriaForm,
                    DespachoInicialForm, DocumentoAcessorioForm,
                    LegislacaoCitadaForm, MateriaLegislativaFilterSet,
                    NumeracaoForm, ProposicaoForm, RelatoriaForm,
                    TramitacaoForm, UnidadeTramitacaoForm,
                    filtra_tramitacao_destino,
                    filtra_tramitacao_destino_and_status,
                    filtra_tramitacao_status)
from .models import (AcompanhamentoMateria, Anexada, Autor, Autoria,
                     DespachoInicial, DocumentoAcessorio, MateriaLegislativa,
                     Numeracao, Orgao, Origem, Proposicao, RegimeTramitacao,
                     Relatoria, StatusTramitacao, TipoAutor, TipoDocumento,
                     TipoFimRelatoria, TipoMateriaLegislativa, TipoProposicao,
                     Tramitacao, UnidadeTramitacao)

OrigemCrud = Crud.build(Origem, 'origem')
TipoMateriaCrud = Crud.build(TipoMateriaLegislativa,
                             'tipo_materia_legislativa')
RegimeTramitacaoCrud = Crud.build(RegimeTramitacao, 'regime_tramitacao')
TipoDocumentoCrud = Crud.build(TipoDocumento, 'tipo_documento')
TipoFimRelatoriaCrud = Crud.build(TipoFimRelatoria, 'fim_relatoria')
AnexadaCrud = Crud.build(Anexada, '')
TipoAutorCrud = Crud.build(TipoAutor, 'tipo_autor')
AutorCrud = Crud.build(Autor, 'autor')
OrgaoCrud = Crud.build(Orgao, 'orgao')
TipoProposicaoCrud = Crud.build(TipoProposicao, 'tipo_proposicao')
StatusTramitacaoCrud = Crud.build(StatusTramitacao, 'status_tramitacao')


class UnidadeTramitacaoCrud(Crud):
    model = UnidadeTramitacao
    help_path = 'unidade_tramitacao'

    class CreateView(crud.base.CrudCreateView):
        form_class = UnidadeTramitacaoForm

    class UpdateView(crud.base.CrudUpdateView):
        form_class = UnidadeTramitacaoForm


class ProposicaoCrud(Crud):
    model = Proposicao
    help_path = ''

    class BaseMixin(crud.base.CrudBaseMixin):
        list_field_names = ['data_envio', 'descricao', 'tipo']

    class CreateView(crud.base.CrudCreateView):
        form_class = ProposicaoForm

        @property
        def layout_key(self):
            return 'ProposicaoCreate'

    class UpdateView(crud.base.CrudUpdateView):
        form_class = ProposicaoForm

        @property
        def layout_key(self):
            return 'ProposicaoCreate'

    class ListView(crud.base.CrudListView):
        ordering = ['-data_envio', 'descricao']

        def get_rows(self, object_list):

            for obj in object_list:
                if obj.data_envio is None:
                    obj.data_envio = 'Em elaboração...'

            return [self._as_row(obj) for obj in object_list]

    class DeleteView(MasterDetailCrud.DeleteView):

        def delete(self, request, *args, **kwargs):
            proposicao = Proposicao.objects.get(id=self.kwargs['pk'])

            if not proposicao.data_envio:
                proposicao.delete()
                return HttpResponseRedirect(reverse('materia:proposicao_list'))
            else:
                proposicao.data_envio = None
                proposicao.save()
                return HttpResponseRedirect(
                    reverse('materia:proposicao_detail',
                            kwargs={'pk': proposicao.pk}))


class RelatoriaCrud(MasterDetailCrud):
    model = Relatoria
    parent_field = 'materia'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = RelatoriaForm

        def get_initial(self):
            materia = MateriaLegislativa.objects.get(id=self.kwargs['pk'])

            loc_atual = Tramitacao.objects.filter(
                materia=materia).last()

            if loc_atual is None:
                localizacao = 0
            else:
                comissao = loc_atual.unidade_tramitacao_destino.comissao
                if comissao:
                    localizacao = comissao.pk
                else:
                    localizacao = 0

            return {'comissao': localizacao}

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = RelatoriaForm


class TramitacaoCrud(MasterDetailCrud):
    model = Tramitacao
    parent_field = 'materia'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = TramitacaoForm

    class ListView(MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao')

    class DeleteView(MasterDetailCrud.DeleteView):

        def delete(self, request, *args, **kwargs):
            tramitacao = Tramitacao.objects.get(id=self.kwargs['pk'])
            materia = MateriaLegislativa.objects.get(id=tramitacao.materia.id)
            url = reverse('materia:tramitacao_list',
                          kwargs={'pk': tramitacao.materia.id})

            if tramitacao.pk != materia.tramitacao_set.last().pk:
                msg = _('Somente a útlima tramitação pode ser deletada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(url)
            else:
                tramitacao.delete()
                return HttpResponseRedirect(url)


def montar_row_autor():
    autor_row = crispy_layout_mixin.to_row(
        [('autor', 0),
         (Button('pesquisar',
                 'Pesquisar Autor',
                 css_class='btn btn-primary btn-sm'), 2),
         (Button('limpar',
                 'Limpar Autor',
                 css_class='btn btn-primary btn-sm'), 10)])

    return autor_row


def montar_helper_documento_acessorio(self):
    autor_row = montar_row_autor()
    self.helper = FormHelper()
    self.helper.layout = crispy_layout_mixin.SaplFormLayout(
        *self.get_layout())

    # Adiciona o novo campo 'autor' e mecanismo de busca
    self.helper.layout[0][0].append(HTML(sapl.utils.autor_label))
    self.helper.layout[0][0].append(HTML(sapl.utils.autor_modal))
    self.helper.layout[0][1] = autor_row

    # Remove botões que estão fora do form
    self.helper.layout[1].pop()

    # Adiciona novos botões dentro do form
    self.helper.layout[0][3][0].insert(1, form_actions(more=[
        HTML('<a href="{{ view.cancel_url }}"'
             ' class="btn btn-inverse">Cancelar</a>')]))


class DocumentoAcessorioCrud(MasterDetailCrud):
    model = DocumentoAcessorio
    parent_field = 'materia'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'tipo', 'data', 'autor', 'arquivo']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DocumentoAcessorioForm

        def __init__(self, *args, **kwargs):
            montar_helper_documento_acessorio(self)
            super(CreateView, self).__init__(*args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super(CreateView, self).get_context_data(**kwargs)
            context['helper'] = self.helper
            return context

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = DocumentoAcessorioForm

        def __init__(self, *args, **kwargs):
            montar_helper_documento_acessorio(self)
            super(UpdateView, self).__init__(*args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super(UpdateView, self).get_context_data(**kwargs)
            context['helper'] = self.helper
            return context


class AutoriaCrud(MasterDetailCrud):
    model = Autoria
    parent_field = 'materia'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = AutoriaForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = AutoriaForm


class DespachoInicialCrud(MasterDetailCrud):
    model = DespachoInicial
    parent_field = 'materia'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DespachoInicialForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = DespachoInicialForm


class LegislacaoCitadaCrud(MasterDetailCrud):
    model = LegislacaoCitada
    parent_field = 'materia'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['norma', 'disposicoes']

        def resolve_url(self, suffix, args=None):
            namespace = 'materia'
            return reverse('%s:%s' % (namespace, self.url_name(suffix)),
                           args=args)

    class CreateView(MasterDetailCrud.CreateView):
        form_class = LegislacaoCitadaForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = LegislacaoCitadaForm

        def get_initial(self):
            self.initial['tipo'] = self.object.norma.tipo.id
            self.initial['numero'] = self.object.norma.numero
            self.initial['ano'] = self.object.norma.ano
            return self.initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'LegislacaoCitadaDetail'


class NumeracaoCrud(MasterDetailCrud):
    model = Numeracao
    parent_field = 'materia'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):
        form_class = NumeracaoForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = NumeracaoForm


class AnexadaCrud(MasterDetailCrud):
    model = Anexada
    parent_field = 'materia_principal'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['materia_anexada', 'data_anexacao']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = AnexadaForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = AnexadaForm

        def get_initial(self):
            self.initial['tipo'] = self.object.materia_anexada.tipo.id
            self.initial['numero'] = self.object.materia_anexada.numero
            self.initial['ano'] = self.object.materia_anexada.ano

            return self.initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'AnexadaDetail'


class MateriaLegislativaCrud(Crud):
    model = MateriaLegislativa
    help_path = 'materia_legislativa'

    class BaseMixin(crud.base.CrudBaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data_apresentacao']


class DocumentoAcessorioView(CreateView):
    template_name = "materia/documento_acessorio.html"
    form_class = DocumentoAcessorioForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        docs = DocumentoAcessorio.objects.filter(
            materia_id=kwargs['pk']).order_by('data')
        form = DocumentoAcessorioForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'docs': docs})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        docs_list = DocumentoAcessorio.objects.filter(
            materia_id=kwargs['pk'])

        if form.is_valid():
            documento_acessorio = form.save(commit=False)
            documento_acessorio.materia = materia
            documento_acessorio.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'docs': docs_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:documento_acessorio', kwargs={'pk': pk})


class AcompanhamentoConfirmarView(TemplateView):

    def get_redirect_url(self):
        return reverse("sessao:list_pauta_sessao")

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')

        acompanhar = AcompanhamentoMateria.objects.get(materia_id=materia_id,
                                                       hash=hash_txt)
        acompanhar.confirmado = True
        acompanhar.save()

        return HttpResponseRedirect(self.get_redirect_url())


class AcompanhamentoExcluirView(TemplateView):

    def get_redirect_url(self):
        return reverse("sessao:list_pauta_sessao")

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')

        try:
            AcompanhamentoMateria.objects.get(materia_id=materia_id,
                                              hash=hash_txt).delete()
        except ObjectDoesNotExist:
            pass

        return HttpResponseRedirect(self.get_redirect_url())


class MateriaLegislativaPesquisaView(FilterView):
    model = MateriaLegislativa
    filterset_class = MateriaLegislativaFilterSet
    paginate_by = 10

    def get_filterset_kwargs(self, filterset_class):
        super(MateriaLegislativaPesquisaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        status_tramitacao = self.request.GET.get('tramitacao__status')
        unidade_destino = self.request.GET.get(
            'tramitacao__unidade_tramitacao_destino')

        qs = self.get_queryset()

        if status_tramitacao and unidade_destino:
            lista = filtra_tramitacao_destino_and_status(status_tramitacao,
                                                         unidade_destino)
            qs = qs.filter(id__in=lista).distinct()

        elif status_tramitacao:
            lista = filtra_tramitacao_status(status_tramitacao)
            qs = qs.filter(id__in=lista).distinct()

        elif unidade_destino:
            lista = filtra_tramitacao_destino(unidade_destino)
            qs = qs.filter(id__in=lista).distinct()

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(MateriaLegislativaPesquisaView,
                        self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        return context

    def get(self, request, *args, **kwargs):
        super(MateriaLegislativaPesquisaView, self).get(request)

        # Se a pesquisa estiver quebrando com a paginação
        # Olhe esta função abaixo
        # Provavelmente você criou um novo campo no Form/FilterSet
        # Então a ordem da URL está diferente
        data = self.filterset.data
        if (data and data.get('tipo') is not None):
            url = "&"+str(self.request.environ['QUERY_STRING'])
            if url.startswith("&page"):
                ponto_comeco = url.find('tipo=') - 1
                url = url[ponto_comeco:]
        else:
            url = ''

        self.filterset.form.fields['o'].label = _('Ordenação')

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list,
                                        filter_url=url,
                                        numero_res=len(self.object_list)
                                        )

        return self.render_to_response(context)


class MateriaTaView(IntegracaoTaView):
    model = MateriaLegislativa
    model_type_foreignkey = TipoMateriaLegislativa


class ProposicaoTaView(IntegracaoTaView):
    model = Proposicao
    model_type_foreignkey = TipoProposicao


class AcompanhamentoMateriaView(CreateView):
    template_name = "materia/acompanhamento_materia.html"

    def get_random_chars(self):
        s = ascii_letters + digits
        return ''.join(choice(s) for i in range(choice([6, 7])))

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        materia = MateriaLegislativa.objects.get(id=pk)

        return self.render_to_response(
            {'form': AcompanhamentoMateriaForm(),
             'materia': materia})

    def post(self, request, *args, **kwargs):
        form = AcompanhamentoMateriaForm(request.POST)
        pk = self.kwargs['pk']
        materia = MateriaLegislativa.objects.get(id=pk)

        if form.is_valid():

            email = form.cleaned_data['email']
            usuario = request.user

            hash_txt = self.get_random_chars()

            try:
                AcompanhamentoMateria.objects.get(
                    email=email,
                    materia=materia,
                    hash=hash_txt)
            except ObjectDoesNotExist:
                acompanhar = form.save(commit=False)
                acompanhar.hash = hash_txt
                acompanhar.materia = materia
                acompanhar.usuario = usuario.username
                acompanhar.confirmado = False
                acompanhar.save()

                do_envia_email_confirmacao(request, materia, email)

            else:
                return self.render_to_response(
                    {'form': form,
                     'materia': materia,
                     'error': _('Essa matéria já está\
                     sendo acompanhada por este e-mail.')})
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'materia': materia})

    def get_success_url(self):
        return reverse('sessao:list_pauta_sessao')
