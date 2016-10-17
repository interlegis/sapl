from datetime import datetime
from random import choice
from string import ascii_letters, digits

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.template import Context, loader
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from django.views.generic.base import RedirectView
from django_filters.views import FilterView

from sapl.base.models import AppConfig, Autor, CasaLegislativa, TipoAutor
from sapl.compilacao.views import IntegracaoTaView
from sapl.crispy_layout_mixin import SaplFormLayout, form_actions
from sapl.crud.base import (ACTION_CREATE, ACTION_DELETE, ACTION_DETAIL,
                            ACTION_LIST, ACTION_UPDATE, RP_DETAIL, RP_LIST,
                            Crud, CrudAux, CrudDetailView, MasterDetailCrud,
                            make_pagination)
from sapl.materia import apps
from sapl.materia.forms import AnexadaForm, LegislacaoCitadaForm,\
    TipoProposicaoForm, ProposicaoCreateForm
from sapl.norma.models import LegislacaoCitada
from sapl.utils import (TURNO_TRAMITACAO_CHOICES, YES_NO_CHOICES, autor_label,
                        autor_modal, gerar_hash_arquivo, get_base_url,
                        permissoes_autor, permissoes_materia,
                        permissoes_protocoloadm, permission_required_for_app,
                        montar_row_autor)

from .forms import (AcessorioEmLoteFilterSet, AcompanhamentoMateriaForm,
                    ConfirmarProposicaoForm, DocumentoAcessorioForm,
                    MateriaLegislativaFilterSet,
                    PrimeiraTramitacaoEmLoteFilterSet, ProposicaoOldForm,
                    ReceberProposicaoForm, TramitacaoEmLoteFilterSet,
                    filtra_tramitacao_destino,
                    filtra_tramitacao_destino_and_status,
                    filtra_tramitacao_status)
from .models import (AcompanhamentoMateria, Anexada, Autoria, DespachoInicial,
                     DocumentoAcessorio, MateriaLegislativa, Numeracao, Orgao,
                     Origem, Proposicao, RegimeTramitacao, Relatoria,
                     StatusTramitacao, TipoDocumento, TipoFimRelatoria,
                     TipoMateriaLegislativa, TipoProposicao, Tramitacao,
                     UnidadeTramitacao)

OrigemCrud = Crud.build(Origem, '')

TipoMateriaCrud = CrudAux.build(
    TipoMateriaLegislativa, 'tipo_materia_legislativa')

RegimeTramitacaoCrud = CrudAux.build(
    RegimeTramitacao, 'regime_tramitacao')

TipoDocumentoCrud = CrudAux.build(
    TipoDocumento, 'tipo_documento')

TipoFimRelatoriaCrud = CrudAux.build(
    TipoFimRelatoria, 'fim_relatoria')


class MateriaTaView(IntegracaoTaView):
    model = MateriaLegislativa
    model_type_foreignkey = TipoMateriaLegislativa

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        if AppConfig.attr('texto_articulado_materia'):
            return IntegracaoTaView.get(self, request, *args, **kwargs)
        else:
            return self.get_redirect_deactivated()


class ProposicaoTaView(IntegracaoTaView):
    model = Proposicao
    model_type_foreignkey = TipoProposicao

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        if AppConfig.attr('texto_articulado_proposicao'):
            return IntegracaoTaView.get(self, request, *args, **kwargs)
        else:
            return self.get_redirect_deactivated()


@permission_required_for_app(app_label=apps.AppConfig.label)
def recuperar_materia(request):
    tipo = TipoMateriaLegislativa.objects.get(pk=request.GET['tipo'])
    materia = MateriaLegislativa.objects.filter(tipo=tipo).last()
    if materia:
        response = JsonResponse({'numero': materia.numero + 1,
                                 'ano': datetime.now().year})
    else:
        response = JsonResponse({'numero': 1, 'ano': datetime.now().year})

    return response


class ConfirmarEmailView(TemplateView):
    template_name = "confirma_email.html"

    def get(self, request, *args, **kwargs):
        uid = urlsafe_base64_decode(self.kwargs['uidb64'])
        user = get_user_model().objects.get(id=uid)
        user.is_active = True
        user.save()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


OrgaoCrud = CrudAux.build(Orgao, 'orgao')
StatusTramitacaoCrud = CrudAux.build(StatusTramitacao, 'status_tramitacao')
UnidadeTramitacaoCrud = CrudAux.build(UnidadeTramitacao, 'unidade_tramitacao')


class TipoProposicaoCrud(CrudAux):
    model = TipoProposicao
    help_text = 'tipo_proposicao'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ["descricao", "conteudo", 'tipo_conteudo_related']

    class CreateView(CrudAux.CreateView):
        form_class = TipoProposicaoForm
        layout_key = None

    class UpdateView(CrudAux.UpdateView):
        form_class = TipoProposicaoForm
        layout_key = None


def criar_materia_proposicao(proposicao):
    tipo_materia = TipoMateriaLegislativa.objects.get(
        descricao=proposicao.tipo.descricao)
    numero = MateriaLegislativa.objects.filter(
        ano=datetime.now().year).order_by('numero').last().numero + 1
    regime = RegimeTramitacao.objects.get(descricao='Normal')

    return MateriaLegislativa.objects.create(
        tipo=tipo_materia,
        ano=datetime.now().year,
        numero=numero,
        data_apresentacao=datetime.now(),
        regime_tramitacao=regime,
        em_tramitacao=True,
        ementa=proposicao.descricao,
        texto_original=proposicao.texto_original
    )


def criar_doc_proposicao(proposicao):
    tipo_doc = TipoDocumento.objects.get(
        descricao=proposicao.tipo.descricao)
    if proposicao.autor is None:
        autor = 'Desconhecido'
    else:
        autor = proposicao.autor

    return DocumentoAcessorio.objects.create(
        materia=proposicao.materia,
        tipo=tipo_doc,
        arquivo=proposicao.texto_original,
        nome=proposicao.descricao,
        data=proposicao.data_envio,
        autor=autor
    )


class ProposicaoDevolvida(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_devolvidas_list.html'
    model = Proposicao
    ordering = ['data_envio']
    paginate_by = 10
    permission_required = permissoes_protocoloadm()

    def get_queryset(self):
        return Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=True,
            data_devolucao__isnull=False)

    def get_context_data(self, **kwargs):
        context = super(ProposicaoDevolvida, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context['NO_ENTRIES_MSG'] = 'Nenhuma proposição devolvida.'
        return context


class ProposicaoPendente(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_pendentes_list.html'
    model = Proposicao
    ordering = ['data_envio', 'autor', 'tipo', 'descricao']
    paginate_by = 10
    permission_required = permissoes_protocoloadm()

    def get_queryset(self):
        return Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=True,
            data_devolucao__isnull=True)

    def get_context_data(self, **kwargs):
        context = super(ProposicaoPendente, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context['NO_ENTRIES_MSG'] = 'Nenhuma proposição pendente.'
        return context


class ProposicaoRecebida(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_recebidas_list.html'
    model = Proposicao
    ordering = ['data_envio']
    paginate_by = 10
    permission_required = permissoes_protocoloadm()

    def get_queryset(self):
        return Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=False,
            data_devolucao__isnull=True)

    def get_context_data(self, **kwargs):
        context = super(ProposicaoRecebida, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context['NO_ENTRIES_MSG'] = 'Nenhuma proposição recebida.'
        return context


class ReceberProposicao(PermissionRequiredMixin, CreateView):
    template_name = "materia/receber_proposicao.html"
    form_class = ReceberProposicaoForm
    permission_required = permissoes_protocoloadm()

    def get_context_data(self, **kwargs):
        context = super(ReceberProposicao, self).get_context_data(**kwargs)
        context.update({'form': self.get_form()})
        return context

    def post(self, request, *args, **kwargs):
        form = ReceberProposicaoForm(request.POST)

        if form.is_valid():
            proposicoes = Proposicao.objects.filter(data_envio__isnull=False)

            for proposicao in proposicoes:
                hasher = gerar_hash_arquivo(proposicao.texto_original.path,
                                            str(proposicao.pk))
                if hasher == form.cleaned_data['cod_hash']:
                    return HttpResponseRedirect(
                        reverse('sapl.materia:proposicao-confirmar',
                                kwargs={'pk': proposicao.pk}))

            msg = 'Proposição não encontrada!'
            return self.render_to_response({'form': form, 'msg': msg})
        else:
            return self.render_to_response({'form': form})

    def get_success_url(self):
        return reverse('sapl.materia:receber-proposicao')


class ConfirmarProposicao(PermissionRequiredMixin, CreateView):
    template_name = "materia/confirmar_proposicao.html"
    form_class = ConfirmarProposicaoForm
    permission_required = permissoes_protocoloadm()

    def get_context_data(self, **kwargs):
        context = super(ConfirmarProposicao, self).get_context_data(**kwargs)
        proposicao = Proposicao.objects.get(pk=self.kwargs['pk'])
        context.update({'form': self.get_form(), 'proposicao': proposicao})
        return context

    def post(self, request, *args, **kwargs):
        form = ConfirmarProposicaoForm(request.POST)
        proposicao = Proposicao.objects.get(pk=self.kwargs['pk'])

        if form.is_valid():
            if 'incorporar' in request.POST:
                proposicao.data_recebimento = datetime.now()
                if proposicao.tipo.descricao == 'Parecer':
                    documento = criar_doc_proposicao(proposicao)
                    proposicao.documento_gerado = documento
                    proposicao.save()
                    return HttpResponseRedirect(
                        reverse('sapl.materia:documentoacessorio_update',
                                kwargs={'pk': documento.pk}))
                else:
                    materia = criar_materia_proposicao(proposicao)
                    proposicao.materia_gerada = materia
                    proposicao.save()
                    return HttpResponseRedirect(
                        reverse('sapl.materia:materialegislativa_update',
                                kwargs={'pk': materia.pk}))
            else:
                proposicao.data_devolucao = datetime.now()
                proposicao.save()
                return HttpResponseRedirect(
                    reverse('sapl.materia:proposicao-devolvida'))


class ProposicaoCrud(Crud):
    model = Proposicao
    help_path = ''
    container_field = 'autor__user'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['data_envio', 'descricao',
                            'tipo', 'data_recebimento']

    class ListView(Crud.ListView):
        ordering = ['-data_envio', 'descricao']

        def get_rows(self, object_list):

            for obj in object_list:
                if obj.data_envio is None:
                    obj.data_envio = 'Em elaboração...'
                else:
                    obj.data_envio = obj.data_envio.strftime("%d/%m/%Y %H:%M")
                if obj.data_recebimento is None:
                    obj.data_recebimento = 'Não recebida'
                else:
                    obj.data_recebimento = obj.data_recebimento.strftime(
                        "%d/%m/%Y %H:%M")

            return [self._as_row(obj) for obj in object_list]

    class CreateView(Crud.CreateView):
        form_class = ProposicaoCreateForm
        layout_key = None

        def get_success_url(self):

            tipo_texto = self.request.POST.get('tipo_texto', '')

            if tipo_texto != 'T':
                return Crud.CreateView.get_success_url(self)
            else:
                return reverse('sapl.materia:proposicao_ta',
                               kwargs={'pk': self.object.pk})


class ProposicaoOldCrud(Crud):
    """
    TODO: Entre outros comportamento gerais, mesmo que um usuário tenha
    Perfil de Autor o Crud de proposição não deverá permitir acesso a
    proposições. O acesso só deve ser permitido se existe um Autor registrado
    e vinculado ao usuário. Essa tarefa deve ser realizada nas Tabelas Aux.
    """
    model = Proposicao
    help_path = ''

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['data_envio', 'descricao',
                            'tipo', 'data_recebimento']

    class CreateView(Crud.CreateView):
        form_class = ProposicaoOldForm

        @property
        def layout_key(self):
            return 'ProposicaoCreate'

        def get_initial(self):
            try:
                autor_id = Autor.objects.get(user=self.request.user).id
            except MultipleObjectsReturned:
                msg = _('Este usuário está relacionado a mais de um autor. ' +
                        'Operação cancelada')
                messages.add_message(self.request, messages.ERROR, msg)
                return redirect(self.get_success_url())
            except ObjectDoesNotExist:
                # FIXME: Pensar em uma melhor forma
                tipo = TipoAutor.objects.get(name='Externo')

                autor_id = Autor.objects.create(
                    user=self.request.user,
                    nome=str(self.request.user),
                    tipo=tipo).id
                return {'autor': autor_id}
            else:
                return {'autor': autor_id}

    class UpdateView(Crud.UpdateView):
        form_class = ProposicaoOldForm

        def get_initial(self):
            initial = self.initial.copy()
            if self.object.materia:
                initial['tipo_materia'] = self.object.materia.tipo.id
                initial['numero_materia'] = self.object.materia.numero
                initial['ano_materia'] = self.object.materia.ano
            return initial

        @property
        def layout_key(self):
            return 'ProposicaoCreate'

        def has_permission(self):
            perms = self.get_permission_required()
            if not self.request.user.has_perms(perms):
                return False

            if (Proposicao.objects.filter(
               id=self.kwargs['pk'],
               autor__user_id=self.request.user.id).exists()):
                proposicao = Proposicao.objects.get(
                    id=self.kwargs['pk'],
                    autor__user_id=self.request.user.id)
                if (not proposicao.data_recebimento or
                        proposicao.data_devolucao):
                    return True
                else:
                    msg = _('Essa proposição já foi recebida. ' +
                            'Não pode mais ser editada')
                    messages.add_message(self.request, messages.ERROR, msg)
                    return False

    class DetailView(Crud.DetailView):

        def has_permission(self):
            perms = self.get_permission_required()
            if not self.request.user.has_perms(perms):
                return False

            return (Proposicao.objects.filter(
                id=self.kwargs['pk'],
                autor__user_id=self.request.user.id).exists())

        def get_context_data(self, **kwargs):
            context = CrudDetailView.get_context_data(self, **kwargs)
            context['subnav_template_name'] = ''
            return context

    class ListView(Crud.ListView):
        ordering = ['-data_envio', 'descricao']

        def get_rows(self, object_list):

            for obj in object_list:
                if obj.data_envio is None:
                    obj.data_envio = 'Em elaboração...'
                else:
                    obj.data_envio = obj.data_envio.strftime("%d/%m/%Y %H:%M")
                if obj.data_recebimento is None:
                    obj.data_recebimento = 'Não recebida'
                else:
                    obj.data_recebimento = obj.data_recebimento.strftime(
                        "%d/%m/%Y %H:%M")

            return [self._as_row(obj) for obj in object_list]

        def get_queryset(self):
            # Só tem acesso as Proposicoes criadas por ele que ainda nao foram
            # recebidas ou foram devolvidas
            lista = Proposicao.objects.filter(
                autor__user_id=self.request.user.id)
            lista = lista.filter(
                Q(data_recebimento__isnull=True) |
                Q(data_devolucao__isnull=False))

            return lista

    class DeleteView(Crud.DeleteView):

        def has_permission(self):
            perms = self.get_permission_required()
            if not self.request.user.has_perms(perms):
                return False

            return (Proposicao.objects.filter(
                id=self.kwargs['pk'],
                autor__user_id=self.request.user.id).exists())

        def delete(self, request, *args, **kwargs):
            proposicao = Proposicao.objects.get(id=self.kwargs['pk'])

            if not proposicao.data_envio or proposicao.data_devolucao:
                proposicao.delete()
                return HttpResponseRedirect(
                    reverse('sapl.materia:proposicao_list'))

            elif not proposicao.data_recebimento:
                proposicao.data_envio = None
                proposicao.save()
                return HttpResponseRedirect(
                    reverse('sapl.materia:proposicao_detail',
                            kwargs={'pk': proposicao.pk}))

            else:
                msg = _('Essa proposição já foi recebida. ' +
                        'Não pode mais ser excluída/recuperada')
                messages.add_message(self.request, messages.ERROR, msg)
                return HttpResponseRedirect(
                    reverse('sapl.materia:proposicao_detail',
                            kwargs={'pk': proposicao.pk}))


class ReciboProposicaoView(TemplateView):
    template_name = "materia/recibo_proposicao.html"
    permission_required = permissoes_autor()

    def has_permission(self):
        perms = self.get_permission_required()
        if not self.request.user.has_perms(perms):
            return False

        return (Proposicao.objects.filter(
            id=self.kwargs['pk'],
            autor__user_id=self.request.user.id).exists())

    def get_context_data(self, **kwargs):
        context = super(ReciboProposicaoView, self).get_context_data(
            **kwargs)
        proposicao = Proposicao.objects.get(pk=self.kwargs['pk'])
        context.update({'proposicao': proposicao,
                        'hash': gerar_hash_arquivo(
                            proposicao.texto_original.path,
                            self.kwargs['pk'])})
        return context


class RelatoriaCrud(MasterDetailCrud):
    model = Relatoria
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class CreateView(MasterDetailCrud.CreateView):

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


class TramitacaoCrud(MasterDetailCrud):
    model = Tramitacao
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']
        ordered_list = False
        ordering = '-data_tramitacao',

    class CreateView(MasterDetailCrud.CreateView):

        def get_initial(self):
            local = MateriaLegislativa.objects.get(
                pk=self.kwargs['pk']).tramitacao_set.last()
            if local:
                self.initial['unidade_tramitacao_local'
                             ] = local.unidade_tramitacao_destino.pk
            self.initial['data_tramitacao'] = datetime.now()
            return self.initial

        def post(self, request, *args, **kwargs):
            materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
            do_envia_email_tramitacao(request, materia)
            return super(CreateView, self).post(request, *args, **kwargs)

    class UpdateView(MasterDetailCrud.UpdateView):

        def post(self, request, *args, **kwargs):
            materia = MateriaLegislativa.objects.get(
                tramitacao__id=kwargs['pk'])
            do_envia_email_tramitacao(request, materia)
            return super(UpdateView, self).post(request, *args, **kwargs)

        @property
        def layout_key(self):
            return 'TramitacaoUpdate'

    class ListView(MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao', '-id')

    class DeleteView(MasterDetailCrud.DeleteView):

        def delete(self, request, *args, **kwargs):
            tramitacao = Tramitacao.objects.get(id=self.kwargs['pk'])
            materia = MateriaLegislativa.objects.get(id=tramitacao.materia.id)
            url = reverse('sapl.materia:tramitacao_list',
                          kwargs={'pk': tramitacao.materia.id})

            if tramitacao.pk != materia.tramitacao_set.last().pk:
                msg = _('Somente a última tramitação pode ser deletada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(url)
            else:
                tramitacao.delete()
                return HttpResponseRedirect(url)


def montar_helper_documento_acessorio(self):
    autor_row = montar_row_autor('autor')
    self.helper = FormHelper()
    self.helper.layout = SaplFormLayout(*self.get_layout())

    # Adiciona o novo campo 'autor' e mecanismo de busca
    self.helper.layout[0][0].append(HTML(autor_label))
    self.helper.layout[0][0].append(HTML(autor_modal))
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
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'tipo', 'data', 'autor', 'arquivo']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DocumentoAcessorioForm

        def __init__(self, **kwargs):
            montar_helper_documento_acessorio(self)
            super(MasterDetailCrud.CreateView, self).__init__(**kwargs)

        def get_context_data(self, **kwargs):
            context = super(
                MasterDetailCrud.CreateView, self).get_context_data(**kwargs)
            context['helper'] = self.helper
            return context

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = DocumentoAcessorioForm

        def __init__(self, **kwargs):
            montar_helper_documento_acessorio(self)
            super(MasterDetailCrud.UpdateView, self).__init__(**kwargs)

        def get_context_data(self, **kwargs):
            context = super(UpdateView, self).get_context_data(**kwargs)
            context['helper'] = self.helper
            return context


class AutoriaCrud(MasterDetailCrud):
    model = Autoria
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]


class DespachoInicialCrud(MasterDetailCrud):
    model = DespachoInicial
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]


class LegislacaoCitadaCrud(MasterDetailCrud):
    model = LegislacaoCitada
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['norma', 'disposicoes']

        def resolve_url(self, suffix, args=None):
            namespace = 'sapl.materia'
            return reverse('%s:%s' % (namespace, self.url_name(suffix)),
                           args=args)

        def has_permission(self):
            perms = self.get_permission_required()
            # Torna a view pública se não possuir conteudo
            # no atributo permission_required
            return self.request.user.has_module_perms('materia')\
                if len(perms) else True

        def permission(self, rad):
            return '%s%s%s' % ('norma' if rad.endswith('_') else '',
                               rad,
                               self.model_name if rad.endswith('_') else '')

        @property
        def detail_create_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if self.request.user.has_module_perms('materia'):
                parent_field = obj.parent_field.split('__')[0]
                parent_object = getattr(self.object, parent_field)

                root_pk = parent_object.pk

                return self.resolve_url(ACTION_CREATE, args=(root_pk,))
            return ''

        @property
        def list_url(self):
            return self.resolve_url(ACTION_LIST, args=(self.kwargs['pk'],))\
                if self.request.user.has_module_perms('materia') else ''

        @property
        def create_url(self):
            return self.resolve_url(ACTION_CREATE, args=(self.kwargs['pk'],))\
                if self.request.user.has_module_perms('materia') else ''

        @property
        def detail_url(self):
            return self.resolve_url(ACTION_DETAIL, args=(self.object.id,))\
                if self.request.user.has_module_perms('materia') else ''

        @property
        def update_url(self):
            return self.resolve_url(ACTION_UPDATE, args=(self.kwargs['pk'],))\
                if self.request.user.has_module_perms('materia') else ''

        @property
        def delete_url(self):
            return self.resolve_url(ACTION_DELETE, args=(self.object.id,))\
                if self.request.user.has_module_perms('materia') else ''

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

    class DeleteView(MasterDetailCrud.DeleteView):
        pass


class NumeracaoCrud(MasterDetailCrud):
    model = Numeracao
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]


class AnexadaCrud(MasterDetailCrud):
    model = Anexada
    parent_field = 'materia_principal'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

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
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data_apresentacao']

        @property
        def list_url(self):
            return ''

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesquisar_materia'))

    class CreateView(Crud.CreateView):

        @property
        def cancel_url(self):
            return self.search_url

    class ListView(Crud.ListView, RedirectView):

        def get_redirect_url(self, *args, **kwargs):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesquisar_materia'))

        def get(self, request, *args, **kwargs):
            return RedirectView.get(self, request, *args, **kwargs)


# FIXME - qual a finalidade dessa classe??
class DocumentoAcessorioView(PermissionRequiredMixin, CreateView):
    template_name = "materia/documento_acessorio.html"
    form_class = DocumentoAcessorioForm
    permission_required = permissoes_materia()

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
        return reverse('sapl.materia:documento_acessorio', kwargs={'pk': pk})


class AcompanhamentoConfirmarView(PermissionRequiredMixin, TemplateView):
    permission_required = permissoes_materia()

    def get_redirect_url(self):
        return reverse('sapl.sessao:list_pauta_sessao')

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')

        acompanhar = AcompanhamentoMateria.objects.get(materia_id=materia_id,
                                                       hash=hash_txt)
        acompanhar.confirmado = True
        acompanhar.save()

        return HttpResponseRedirect(self.get_redirect_url())


class AcompanhamentoExcluirView(PermissionRequiredMixin, TemplateView):
    permission_required = permissoes_materia()

    def get_redirect_url(self):
        return reverse('sapl.sessao:list_pauta_sessao')

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

        context['title'] = _('Pesquisar Matéria Legislativa')

        self.filterset.form.fields['o'].label = _('Ordenação')

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        return context


class AcompanhamentoMateriaView(PermissionRequiredMixin, CreateView):
    template_name = "materia/acompanhamento_materia.html"
    permission_required = permissoes_materia()

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
        return reverse('sapl.sessao:list_pauta_sessao')


def load_email_templates(templates, context={}):

    emails = []
    for t in templates:
        tpl = loader.get_template(t)
        email = tpl.render(Context(context))
        if t.endswith(".html"):
            email = email.replace('\n', '').replace('\r', '')
        emails.append(email)
    return emails


def criar_email_confirmacao(request, casa_legislativa, materia, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not materia:
        raise ValueError("Matéria é obrigatória")

    # FIXME i18n
    casa_nome = (casa_legislativa.nome + ' de ' +
                 casa_legislativa.municipio + '-' +
                 casa_legislativa.uf)

    base_url = get_base_url(request)
    materia_url = reverse('sapl.materia:acompanhar_materia',
                          kwargs={'pk': materia.id})
    confirmacao_url = reverse('sapl.materia:acompanhar_confirmar',
                              kwargs={'pk': materia.id})

    autores = []
    for autoria in materia.autoria_set.all():
        autores.append(autoria.autor.nome)

    templates = load_email_templates(['email/acompanhar.txt',
                                      'email/acompanhar.html'],
                                     {"casa_legislativa": casa_nome,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_materia": materia.ementa,
                                      "autoria": autores,
                                      "hash_txt": hash_txt,
                                      "base_url": base_url,
                                      "materia": str(materia),
                                      "materia_url": materia_url,
                                      "confirmacao_url": confirmacao_url, })
    return templates


def criar_email_tramitacao(request, casa_legislativa, materia, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not materia:
        raise ValueError("Matéria é obrigatória")

    # FIXME i18n
    casa_nome = (casa_legislativa.nome + ' de ' +
                 casa_legislativa.municipio + '-' +
                 casa_legislativa.uf)

    base_url = get_base_url(request)
    url_materia = reverse('sapl.materia:acompanhar_materia',
                          kwargs={'pk': materia.id})
    url_excluir = reverse('sapl.materia:acompanhar_excluir',
                          kwargs={'pk': materia.id})

    autores = []
    for autoria in materia.autoria_set.all():
        autores.append(autoria.autor.nome)

    templates = load_email_templates(['email/tramitacao.txt',
                                      'email/tramitacao.html'],
                                     {"casa_legislativa": casa_nome,
                                      "data_registro": datetime.now().strftime(
                                          "%d/%m/%Y"),
                                      "cod_materia": materia.id,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_materia": materia.ementa,
                                      "autoria": autores,
                                      "data": materia.tramitacao_set.last(
                                      ).data_tramitacao,
                                      "status": materia.tramitacao_set.last(
                                      ).status,
                                      "texto_acao":
                                         materia.tramitacao_set.last().texto,
                                      "hash_txt": hash_txt,
                                      "materia": str(materia),
                                      "base_url": base_url,
                                      "materia_url": url_materia,
                                      "excluir_url": url_excluir})
    return templates


def enviar_emails(sender, recipients, messages):
    '''
        Recipients is a string list of email addresses

        Messages is an array of dicts of the form:
        {'recipient': 'address', # useless????
         'subject': 'subject text',
         'txt_message': 'text message',
         'html_message': 'html message'
        }
    '''

    if len(messages) == 1:
        # sends an email simultaneously to all recipients
        send_mail(messages[0]['subject'],
                  messages[0]['txt_message'],
                  sender,
                  recipients,
                  html_message=messages[0]['html_message'],
                  fail_silently=False)

    elif len(recipients) > len(messages):
        raise ValueError("Message list should have size 1 \
                         or equal recipient list size. \
                         recipients: %s, messages: %s" % (recipients, messages)
                         )

    else:
        # sends an email simultaneously to all reciepients
        for (d, m) in zip(recipients, messages):
            send_mail(m['subject'],
                      m['txt_message'],
                      sender,
                      [d],
                      html_message=m['html_message'],
                      fail_silently=False)
    return None


def do_envia_email_confirmacao(request, materia, email):
    #
    # Envia email de confirmacao para atualizações de tramitação
    #
    destinatario = AcompanhamentoMateria.objects.get(materia=materia,
                                                     email=email,
                                                     confirmado=False)
    casa = CasaLegislativa.objects.first()

    sender = 'sapl-test@interlegis.leg.br'
    # FIXME i18n
    subject = "[SAPL] " + str(materia) + " - Ative o Acompanhamento da Materia"
    messages = []
    recipients = []

    email_texts = criar_email_confirmacao(request,
                                          casa,
                                          materia,
                                          destinatario.hash,)
    recipients.append(destinatario.email)
    messages.append({
        'recipient': destinatario.email,
        'subject': subject,
        'txt_message': email_texts[0],
        'html_message': email_texts[1]
    })

    enviar_emails(sender, recipients, messages)
    return None


def do_envia_email_tramitacao(request, materia):
    #
    # Envia email de tramitacao para usuarios cadastrados
    #
    destinatarios = AcompanhamentoMateria.objects.filter(materia=materia,
                                                         confirmado=True)
    casa = CasaLegislativa.objects.first()

    sender = 'sapl-test@interlegis.leg.br'
    # FIXME i18n
    subject = "[SAPL] " + str(materia) + \
              " - Acompanhamento de Materia Legislativa"
    messages = []
    recipients = []
    for destinatario in destinatarios:
        email_texts = criar_email_tramitacao(request,
                                             casa,
                                             materia,
                                             destinatario.hash,)
        recipients.append(destinatario.email)
        messages.append({
            'recipient': destinatario.email,
            'subject': subject,
            'txt_message': email_texts[0],
            'html_message': email_texts[1]
        })

    enviar_emails(sender, recipients, messages)
    return None


class DocumentoAcessorioEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = AcessorioEmLoteFilterSet
    template_name = 'materia/em_lote/acessorio.html'
    permission_required = permissoes_materia()

    def get_context_data(self, **kwargs):
        context = super(DocumentoAcessorioEmLoteView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Documentos Acessórios em Lote')
        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        qr = self.request.GET.copy()
        context['tipos_docs'] = TipoDocumento.objects.all()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
        return context

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')

        if len(marcadas) == 0:
            msg = _('Nenhuma máteria foi selecionada.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        tipo = TipoDocumento.objects.get(descricao=request.POST['tipo'])

        for materia_id in marcadas:
            DocumentoAcessorio.objects.create(
                materia_id=materia_id,
                tipo=tipo,
                arquivo=request.POST['arquivo'],
                nome=request.POST['nome'],
                data=datetime.strptime(request.POST['data'], "%d/%m/%Y"),
                autor=Autor.objects.get(id=request.POST['autor']),
                ementa=request.POST['ementa']
            )
        msg = _('Documento(s) criado(s).')
        messages.add_message(request, messages.SUCCESS, msg)
        return self.get(request, self.kwargs)


class PrimeiraTramitacaoEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = PrimeiraTramitacaoEmLoteFilterSet
    template_name = 'materia/em_lote/tramitacao.html'
    permission_required = permissoes_materia()

    def get_context_data(self, **kwargs):
        context = super(PrimeiraTramitacaoEmLoteView,
                        self).get_context_data(**kwargs)

        context['subnav_template_name'] = 'materia/em_lote/subnav_em_lote.yaml'

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        context['title'] = _('Primeira Tramitação em Lote')

        qr = self.request.GET.copy()
        context['unidade_destino'] = UnidadeTramitacao.objects.all()
        context['status_tramitacao'] = StatusTramitacao.objects.all()
        context['turnos_tramitacao'] = TURNO_TRAMITACAO_CHOICES
        context['urgente_tramitacao'] = YES_NO_CHOICES
        context['unidade_local'] = UnidadeTramitacao.objects.all()

        # Pega somente matéria que não possuem tramitação
        if (type(self.__dict__['filterset']).__name__ ==
                'PrimeiraTramitacaoEmLoteFilterSet'):
            context['object_list'] = context['object_list'].filter(
                tramitacao__isnull=True)
        else:
            context['title'] = _('Tramitação em Lote')
            context['unidade_local'] = [UnidadeTramitacao.objects.get(
                id=qr['tramitacao__unidade_tramitacao_destino'])]

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
        return context

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')

        if len(marcadas) == 0:
            msg = _('Nenhuma máteria foi selecionada.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        if request.POST['data_encaminhamento']:
            data_encaminhamento = datetime.strptime(
                request.POST['data_encaminhamento'], "%d/%m/%Y")
        else:
            data_encaminhamento = None

        if request.POST['data_fim_prazo']:
            data_fim_prazo = datetime.strptime(
                request.POST['data_fim_prazo'], "%d/%m/%Y")
        else:
            data_fim_prazo = None

        for materia_id in marcadas:
            Tramitacao.objects.create(
                materia_id=materia_id,
                data_tramitacao=datetime.strptime(
                    request.POST['data_tramitacao'], "%d/%m/%Y"),
                data_encaminhamento=data_encaminhamento,
                data_fim_prazo=data_fim_prazo,
                unidade_tramitacao_local_id=request.POST[
                    'unidade_tramitacao_local'],
                unidade_tramitacao_destino_id=request.POST[
                    'unidade_tramitacao_destino'],
                urgente=request.POST['urgente'],
                status_id=request.POST['status'],
                turno=request.POST['turno'],
                texto=request.POST['texto']
            )
        msg = _('Tramitação completa.')
        messages.add_message(request, messages.SUCCESS, msg)
        return self.get(request, self.kwargs)


class TramitacaoEmLoteView(PrimeiraTramitacaoEmLoteView):
    filterset_class = TramitacaoEmLoteFilterSet
