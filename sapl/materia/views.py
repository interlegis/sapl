from datetime import datetime
from random import choice
from string import ascii_letters, digits

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template import Context, loader
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from django.views.generic.base import RedirectView
from django.views.generic.edit import FormView
from django_filters.views import FilterView

from sapl.base.models import Autor, CasaLegislativa
from sapl.comissoes.models import Comissao, Participacao
from sapl.compilacao.models import (STATUS_TA_IMMUTABLE_RESTRICT,
                                    STATUS_TA_PRIVATE)
from sapl.compilacao.views import IntegracaoTaView
from sapl.crispy_layout_mixin import SaplFormLayout, form_actions
from sapl.crud.base import (ACTION_CREATE, ACTION_DELETE, ACTION_DETAIL,
                            ACTION_LIST, ACTION_UPDATE, RP_DETAIL, RP_LIST,
                            Crud, CrudAux, MasterDetailCrud,
                            PermissionRequiredForAppCrudMixin, make_pagination)
from sapl.materia.forms import (AnexadaForm, ConfirmarProposicaoForm,
                                LegislacaoCitadaForm, ProposicaoForm,
                                TipoProposicaoForm, TramitacaoForm,
                                TramitacaoUpdateForm)
from sapl.norma.models import LegislacaoCitada
from sapl.protocoloadm.models import Protocolo
from sapl.settings import EMAIL_SEND_USER
from sapl.utils import (TURNO_TRAMITACAO_CHOICES, YES_NO_CHOICES, autor_label,
                        autor_modal, gerar_hash_arquivo, get_base_url,
                        montar_row_autor)
import sapl

from .forms import (AcessorioEmLoteFilterSet, AcompanhamentoMateriaForm,
                    AdicionarVariasAutoriasFilterSet, DespachoInicialForm,
                    DocumentoAcessorioForm, MateriaAssuntoForm,
                    MateriaLegislativaFilterSet, MateriaSimplificadaForm,
                    PrimeiraTramitacaoEmLoteFilterSet, ReceberProposicaoForm,
                    RelatoriaForm, TramitacaoEmLoteFilterSet,
                    filtra_tramitacao_destino,
                    filtra_tramitacao_destino_and_status,
                    filtra_tramitacao_status)
from .models import (AcompanhamentoMateria, Anexada, AssuntoMateria, Autoria,
                     DespachoInicial, DocumentoAcessorio, MateriaAssunto,
                     MateriaLegislativa, Numeracao, Orgao, Origem, Proposicao,
                     RegimeTramitacao, Relatoria, StatusTramitacao,
                     TipoDocumento, TipoFimRelatoria, TipoMateriaLegislativa,
                     TipoProposicao, Tramitacao, UnidadeTramitacao)


AssuntoMateriaCrud = Crud.build(AssuntoMateria, 'assunto_materia')

OrigemCrud = Crud.build(Origem, '')

TipoMateriaCrud = CrudAux.build(
    TipoMateriaLegislativa, 'tipo_materia_legislativa')

RegimeTramitacaoCrud = CrudAux.build(
    RegimeTramitacao, 'regime_tramitacao')

TipoDocumentoCrud = CrudAux.build(
    TipoDocumento, 'tipo_documento')

TipoFimRelatoriaCrud = CrudAux.build(
    TipoFimRelatoria, 'fim_relatoria')


def autores_ja_adicionados(materia_pk):
    autorias = Autoria.objects.filter(materia_id=materia_pk)
    pks = [a.autor.pk for a in autorias]
    return pks


def proposicao_texto(request, pk):
    proposicao = Proposicao.objects.get(pk=pk)

    if proposicao.texto_original:
        if (not proposicao.data_recebimento and
            proposicao.autor.user_id != request.user.id):
                raise Http404

        arquivo = proposicao.texto_original

        ext = arquivo.name.split('.')[-1]
        mime = ''
        if ext == 'odt':
            mime = 'application/vnd.oasis.opendocument.text'
        else:
            mime = "application/%s" % (ext,)

        with open(arquivo.path, 'rb') as f:
            data = f.read()

        response = HttpResponse(data, content_type='%s' % mime)
        response['Content-Disposition'] = (
            'inline; filename="%s"' % arquivo.name.split('/')[-1])
        return response
    raise Http404


class AdicionarVariasAutorias(PermissionRequiredForAppCrudMixin, FilterView):
    app_label = sapl.materia.apps.AppConfig.label
    filterset_class = AdicionarVariasAutoriasFilterSet
    template_name = 'materia/adicionar_varias_autorias.html'
    model = Autor

    def get_filterset_kwargs(self, filterset_class):
        super(AdicionarVariasAutorias, self).get_filterset_kwargs(
            filterset_class)
        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()
        qs = qs.exclude(
            id__in=autores_ja_adicionados(self.kwargs['pk'])).distinct()

        kwargs.update({'queryset': qs})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(AdicionarVariasAutorias, self).get_context_data(
            **kwargs)

        context['title'] = _('Pesquisar Autores')
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
        context['pk_materia'] = self.kwargs['pk']
        return context

    def post(self, request, *args, **kwargs):
        marcados = request.POST.getlist('autor_id')

        for m in marcados:
            Autoria.objects.create(
                materia_id=self.kwargs['pk'],
                autor_id=m
            )

        return HttpResponseRedirect(
            reverse('sapl.materia:autoria_list',
                    kwargs={'pk': self.kwargs['pk']}))


class CriarProtocoloMateriaView(CreateView):
    template_name = "crud/form.html"
    form_class = MateriaSimplificadaForm
    form_valid_message = _('Matéria cadastrada com sucesso!')

    def get_success_url(self, materia):
        return reverse('sapl.materia:materialegislativa_detail', kwargs={
            'pk': materia.pk})

    def get_context_data(self, **kwargs):
        context = super(
            CriarProtocoloMateriaView, self).get_context_data(**kwargs)

        try:
            protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        except ObjectDoesNotExist:
            raise Http404()

        materias_ano = MateriaLegislativa.objects.filter(
            ano=protocolo.ano,
            tipo=protocolo.tipo_materia).order_by('-numero')

        if materias_ano:
            numero = materias_ano.first().numero + 1
        else:
            numero = 1

        context['form'].fields['tipo'].initial = protocolo.tipo_materia
        context['form'].fields['numero'].initial = numero
        context['form'].fields['ano'].initial = protocolo.ano
        context['form'].fields['data_apresentacao'].initial = protocolo.data
        context['form'].fields['numero_protocolo'].initial = protocolo.numero
        context['form'].fields['ementa'].initial = protocolo.assunto_ementa

        return context

    def form_valid(self, form):
        materia = form.save()

        try:
            protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        except ObjectDoesNotExist:
            raise Http404()

        if protocolo.autor:
            Autoria.objects.create(
                materia=materia,
                autor=protocolo.autor,
                primeiro_autor=True)

        return redirect(self.get_success_url(materia))


class MateriaTaView(IntegracaoTaView):
    model = MateriaLegislativa
    model_type_foreignkey = TipoMateriaLegislativa
    map_fields = {
        'data': 'data_apresentacao',
        'ementa': 'ementa',
        'observacao': None,
        'numero': 'numero',
        'ano': 'ano',
    }
    map_funcs = {
        'publicacao_func': False,
    }
    ta_values = {
        'editable_only_by_owners': False,
        'editing_locked': False,
    }

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        if sapl.base.models.AppConfig.attr('texto_articulado_materia'):
            return IntegracaoTaView.get(self, request, *args, **kwargs)
        else:
            return self.get_redirect_deactivated()


class ProposicaoTaView(IntegracaoTaView):
    model = Proposicao
    model_type_foreignkey = TipoProposicao
    map_fields = {
        'data': 'data_envio',
        'ementa': 'descricao',
        'observacao': None,
        'numero': 'numero_proposicao',
        'ano': 'ano',
    }
    map_funcs = {
        'publicacao_func': False
    }
    ta_values = {
        'editable_only_by_owners': True,
        'editing_locked': False,
        'privacidade': STATUS_TA_PRIVATE
    }

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        if sapl.base.models.AppConfig.attr('texto_articulado_proposicao'):

            proposicao = get_object_or_404(self.model, pk=kwargs['pk'])

            if not proposicao.data_envio and\
                    request.user != proposicao.autor.user:
                raise Http404()

            return IntegracaoTaView.get(self, request, *args, **kwargs)
        else:
            return self.get_redirect_deactivated()


@permission_required('materia.detail_materialegislativa')
def recuperar_materia(request):
    tipo = TipoMateriaLegislativa.objects.get(pk=request.GET['tipo'])
    ano = request.GET.get('ano', '')

    param = {'tipo': tipo}
    param['data_apresentacao__year'] = ano if ano else datetime.now().year

    materia = MateriaLegislativa.objects.filter(**param).order_by(
        'tipo', 'ano', 'numero').values_list('numero', 'ano').last()
    if materia:
        response = JsonResponse({'numero': materia[0] + 1,
                                 'ano': materia[1]})
    else:
        response = JsonResponse(
            {'numero': 1, 'ano': ano if ano else datetime.now().year})

    return response


OrgaoCrud = CrudAux.build(Orgao, 'orgao')
StatusTramitacaoCrud = CrudAux.build(StatusTramitacao, 'status_tramitacao')


class TipoProposicaoCrud(CrudAux):
    model = TipoProposicao
    help_text = 'tipo_proposicao'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = [
            "descricao", "content_type", 'tipo_conteudo_related']

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
    permission_required = ('materia.detail_proposicao_devolvida', )

    def get_queryset(self):
        return Proposicao.objects.filter(
            data_envio__isnull=True,
            data_recebimento__isnull=True,
            data_devolucao__isnull=False)

    def get_context_data(self, **kwargs):
        context = super(ProposicaoDevolvida, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context['NO_ENTRIES_MSG'] = 'Nenhuma proposição devolvida.'
        context['subnav_template_name'] = 'materia/subnav_prop.yaml'
        return context


class ProposicaoPendente(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_pendentes_list.html'
    model = Proposicao
    ordering = ['data_envio', 'autor', 'tipo', 'descricao']
    paginate_by = 10
    permission_required = ('materia.detail_proposicao_enviada', )

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

        context['subnav_template_name'] = 'materia/subnav_prop.yaml'
        return context


class ProposicaoRecebida(PermissionRequiredMixin, ListView):
    template_name = 'materia/prop_recebidas_list.html'
    model = Proposicao
    ordering = ['data_envio']
    paginate_by = 10
    permission_required = 'materia.detail_proposicao_incorporada'

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
        context['subnav_template_name'] = 'materia/subnav_prop.yaml'
        return context


class ReceberProposicao(PermissionRequiredForAppCrudMixin, FormView):
    app_label = sapl.protocoloadm.apps.AppConfig.label
    template_name = "crud/form.html"
    form_class = ReceberProposicaoForm

    def post(self, request, *args, **kwargs):

        form = ReceberProposicaoForm(request.POST)

        if form.is_valid():
            proposicoes = Proposicao.objects.filter(
                data_envio__isnull=False, data_recebimento__isnull=True)

            for proposicao in proposicoes:
                if proposicao.texto_articulado.exists():
                    ta = proposicao.texto_articulado.first()
                    # FIXME hash para textos articulados
                    hasher = 'P' + ta.hash() + '/' + str(proposicao.id)
                else:
                    hasher = gerar_hash_arquivo(
                        proposicao.texto_original.path,
                        str(proposicao.pk)) \
                        if proposicao.texto_original else None
                if hasher == form.cleaned_data['cod_hash']:
                    return HttpResponseRedirect(
                        reverse('sapl.materia:proposicao-confirmar',
                                kwargs={
                                    'hash': hasher.split('/')[0][1:],
                                    'pk': proposicao.pk}))

            messages.error(request, _('Proposição não encontrada!'))
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('sapl.materia:receber-proposicao')

    def get_context_data(self, **kwargs):
        context = super(ReceberProposicao, self).get_context_data(**kwargs)
        context['subnav_template_name'] = 'materia/subnav_prop.yaml'
        return context


class ConfirmarProposicao(PermissionRequiredForAppCrudMixin, UpdateView):
    app_label = sapl.protocoloadm.apps.AppConfig.label
    template_name = "materia/confirmar_proposicao.html"
    model = Proposicao
    form_class = ConfirmarProposicaoForm

    def get_success_url(self):
        msgs = self.object.results['messages']

        for key, value in msgs.items():
            for item in value:
                getattr(messages, key)(self.request, item)

        return self.object.results['url']

    def get_object(self, queryset=None):
        try:
            """Não deve haver acesso na rotina de confirmação a proposições:
            já recebidas -> data_recebimento != None
            não enviadas -> data_envio == None
            """
            proposicao = Proposicao.objects.get(pk=self.kwargs['pk'],
                                                data_envio__isnull=False,
                                                data_recebimento__isnull=True)
            self.object = None
            # FIXME implementar hash para texto eletrônico

            if proposicao.texto_articulado.exists():
                ta = proposicao.texto_articulado.first()
                # FIXME hash para textos articulados
                hasher = 'P' + ta.hash() + '/' + str(proposicao.id)
            else:
                hasher = gerar_hash_arquivo(
                    proposicao.texto_original.path,
                    str(proposicao.pk)) if proposicao.texto_original else None

            if hasher == 'P%s/%s' % (self.kwargs['hash'], proposicao.pk):
                self.object = proposicao
        except:
            raise Http404()

        if not self.object:
            raise Http404()

        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subnav_template_name'] = ''
        return context


class UnidadeTramitacaoCrud(CrudAux):
    model = UnidadeTramitacao
    help_path = 'unidade_tramitacao'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['comissao', 'orgao', 'parlamentar']

    class ListView(Crud.ListView):
        template_name = "crud/list.html"

        def get_headers(self):
            return [_('Unidade de Tramitação')]

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            for row in context['rows']:
                if row[0][0]:  # Comissão
                    pass
                elif row[1][0]:  # Órgão
                    row[0] = (row[1][0], row[0][1])
                elif row[2][0]:  # Parlamentar
                    row[0] = (row[2][0], row[0][1])
                row[1], row[2] = ('', ''), ('', '')
            return context


class ProposicaoCrud(Crud):
    model = Proposicao
    help_path = ''
    container_field = 'autor__user'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['data_envio', 'data_recebimento', 'descricao',
                            'tipo', 'conteudo_gerado_related']

    class BaseLocalMixin:
        form_class = ProposicaoForm
        layout_key = None

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

        def get(self, request, *args, **kwargs):

            if not self._action_is_valid(request, *args, **kwargs):
                return redirect(reverse('sapl.materia:proposicao_detail',
                                        kwargs={'pk': kwargs['pk']}))
            return super().get(self, request, *args, **kwargs)

        def post(self, request, *args, **kwargs):

            if not self._action_is_valid(request, *args, **kwargs):
                return redirect(reverse('sapl.materia:proposicao_detail',
                                        kwargs={'pk': kwargs['pk']}))
            return super().post(self, request, *args, **kwargs)

    class DetailView(Crud.DetailView):
        layout_key = 'Proposicao'
        permission_required = (RP_DETAIL, 'materia.detail_proposicao_enviada',
                               'materia.detail_proposicao_devolvida',
                               'materia.detail_proposicao_incorporada')

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''

            context['title'] = '%s <small>(%s)</small>' % (
                self.object, self.object.autor)
            return context

        def get(self, request, *args, **kwargs):
            action = request.GET.get('action', '')

            if not action:
                return Crud.DetailView.get(self, request, *args, **kwargs)

            p = Proposicao.objects.get(id=kwargs['pk'])

            msg_error = ''
            if p:
                if action == 'send':
                    if p.data_envio and p.data_recebimento:
                        msg_error = _('Proposição já foi enviada e recebida.')
                    elif p.data_envio:
                        msg_error = _('Proposição já foi enviada.')
                    elif not p.texto_original and\
                            not p.texto_articulado.exists():
                        msg_error = _('Proposição não possui nenhum tipo de '
                                      'Texto associado.')
                    else:
                        p.data_devolucao = None
                        p.data_envio = datetime.now()
                        p.save()

                        if p.texto_articulado.exists():
                            ta = p.texto_articulado.first()
                            ta.privacidade = STATUS_TA_IMMUTABLE_RESTRICT
                            ta.editing_locked = True
                            ta.save()

                        messages.success(request, _(
                            'Proposição enviada com sucesso.'))

                elif action == 'return':
                    if not p.data_envio:
                        msg_error = _('Proposição ainda não foi enviada.')
                    elif p.data_recebimento:
                        msg_error = _('Proposição já foi recebida, não é '
                                      'possível retorná-la.')
                    else:
                        p.data_envio = None
                        p.save()
                        if p.texto_articulado.exists():
                            ta = p.texto_articulado.first()
                            ta.privacidade = STATUS_TA_PRIVATE
                            ta.editing_locked = False
                            ta.save()
                        messages.success(request, _(
                            'Proposição Retornada com sucesso.'))

                if msg_error:
                    messages.error(request, msg_error)

            # retornar redirecionando para limpar a variavel action
            return redirect(reverse('sapl.materia:proposicao_detail',
                                    kwargs={'pk': kwargs['pk']}))

        def dispatch(self, request, *args, **kwargs):

            try:
                p = Proposicao.objects.get(id=kwargs['pk'])
            except:
                raise Http404()

            if not self.has_permission():
                return self.handle_no_permission()

            if p.autor.user != request.user:
                if not p.data_envio and not p.data_devolucao:
                    raise Http404()

                if p.data_devolucao and not request.user.has_perm(
                        'materia.detail_proposicao_devolvida'):
                    raise Http404()

                if p.data_envio and not p.data_recebimento\
                    and not request.user.has_perm(
                        'materia.detail_proposicao_enviada'):
                    raise Http404()

                if p.data_envio and p.data_recebimento\
                    and not request.user.has_perm(
                        'materia.detail_proposicao_incorporada'):
                    raise Http404()

            return super(PermissionRequiredMixin, self).dispatch(
                request, *args, **kwargs)

    class DeleteView(BaseLocalMixin, Crud.DeleteView):

        def _action_is_valid(self, request, *args, **kwargs):
            proposicao = Proposicao.objects.filter(
                id=kwargs['pk']).values_list(
                    'data_envio', 'data_recebimento')

            if proposicao:
                if proposicao[0][0] and proposicao[0][1]:
                    msg = _('Proposição já foi enviada e recebida.'
                            'Não pode mais ser excluida.')
                elif proposicao[0][0] and not proposicao[0][1]:
                    msg = _('Proposição já foi enviada mas ainda não recebida '
                            'pelo protocolo. Use a opção Recuperar Proposição '
                            'para depois excluí-la.')

                if proposicao[0][0] or proposicao[0][1]:
                    messages.error(request, msg)
                    return False
            return True

    class UpdateView(BaseLocalMixin, Crud.UpdateView):

        def _action_is_valid(self, request, *args, **kwargs):

            proposicao = Proposicao.objects.filter(
                id=kwargs['pk']).values_list(
                    'data_envio', 'data_recebimento')

            if proposicao:
                if proposicao[0][0] and proposicao[0][1]:
                    msg = _('Proposição já foi enviada e recebida.'
                            'Não pode mais ser editada')
                elif proposicao[0][0] and not proposicao[0][1]:
                    msg = _('Proposição já foi enviada mas ainda não recebida '
                            'pelo protocolo. Use a opção Recuperar Proposição '
                            'para voltar para edição.')

                if proposicao[0][0] or proposicao[0][1]:
                    messages.error(request, msg)
                    return False
            return True

        def get_success_url(self):

            tipo_texto = self.request.POST.get('tipo_texto', '')

            if tipo_texto == 'T':
                messages.info(self.request,
                              _('Sempre que uma Proposição é inclusa ou '
                                'alterada e a opção "Texto Articulado " for '
                                'marcada, você será redirecionado para a '
                                'edição do Texto Eletrônico.'))
                return reverse('sapl.materia:proposicao_ta',
                               kwargs={'pk': self.object.pk})
            else:
                return Crud.UpdateView.get_success_url(self)

    class CreateView(Crud.CreateView):
        form_class = ProposicaoForm
        layout_key = None

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

        def get_success_url(self):

            tipo_texto = self.request.POST.get('tipo_texto', '')

            if tipo_texto == 'T':
                messages.info(self.request,
                              _('Sempre que uma Proposição é inclusa ou '
                                'alterada e a opção "Texto Articulado " for '
                                'marcada, você será redirecionado para o '
                                'Texto Eletrônico. Use a opção "Editar Texto" '
                                'para construir seu texto.'))
                return reverse('sapl.materia:proposicao_ta',
                               kwargs={'pk': self.object.pk})
            else:
                return Crud.CreateView.get_success_url(self)

    class ListView(Crud.ListView):
        ordering = ['-data_envio', 'descricao']

        def get_rows(self, object_list):

            for obj in object_list:
                if obj.data_recebimento is None:
                    obj.data_recebimento = 'Não recebida'\
                        if obj.data_envio else 'Não enviada'
                else:
                    obj.data_recebimento = formats.date_format(
                        obj.data_recebimento, "DATETIME_FORMAT")

                if obj.data_envio is None:
                    obj.data_envio = 'Em elaboração...'
                else:
                    obj.data_envio = formats.date_format(
                        obj.data_envio, "DATETIME_FORMAT")

            return [self._as_row(obj) for obj in object_list]


class ReciboProposicaoView(TemplateView):
    template_name = "materia/recibo_proposicao.html"
    permission_required = ('materia.detail_proposicao', )

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

        if proposicao.texto_original:
            _hash = gerar_hash_arquivo(
                proposicao.texto_original.path,
                self.kwargs['pk'])
        elif proposicao.texto_articulado.exists():
            ta = proposicao.texto_articulado.first()
            # FIXME hash para textos articulados
            _hash = 'P' + ta.hash() + '/' + str(proposicao.id)

        context.update({'proposicao': proposicao,
                        'hash': _hash})
        return context

    def get(self, request, *args, **kwargs):
        proposicao = Proposicao.objects.get(pk=self.kwargs['pk'])

        if proposicao.data_envio:
            return TemplateView.get(self, request, *args, **kwargs)

        if not proposicao.data_envio and not proposicao.data_devolucao:
            messages.error(request, _('Não é possível gerar recibo para uma '
                                      'Proposição ainda não enviada.'))
        elif proposicao.data_devolucao:
            messages.error(request, _('Não é possível gerar recibo.'))

        return redirect(reverse('sapl.materia:proposicao_detail',
                                kwargs={'pk': proposicao.pk}))


class RelatoriaCrud(MasterDetailCrud):
    model = Relatoria
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = RelatoriaForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            try:
                comissao = Comissao.objects.get(
                    pk=context['form'].initial['comissao'])
            except ObjectDoesNotExist:
                pass
            else:
                composicao = comissao.composicao_set.last()
                participacao = Participacao.objects.filter(
                    composicao=composicao)

                parlamentares = []
                for p in participacao:
                    if p.titular:
                        parlamentares.append(
                            [p.parlamentar.id, p.parlamentar.nome_parlamentar])
                context['form'].fields['parlamentar'].choices = parlamentares

            return context

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
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']
        ordered_list = False
        ordering = '-data_tramitacao',

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoForm

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

            if 'status' in request.POST and request.POST['status']:
                status = StatusTramitacao.objects.filter(
                    id=request.POST['status']).first()
                unidade_destino = UnidadeTramitacao.objects.get(
                    id=request.POST['unidade_tramitacao_destino']
                )
                texto = request.POST['texto']
                data_tramitacao = request.POST['data_tramitacao']
                do_envia_email_tramitacao(
                    request, materia, status,
                    unidade_destino, texto, data_tramitacao)
            return super(CreateView, self).post(request, *args, **kwargs)

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = TramitacaoUpdateForm

        def post(self, request, *args, **kwargs):
            materia = MateriaLegislativa.objects.get(
                tramitacao__id=kwargs['pk'])

            if 'status' in request.POST and request.POST['status']:
                status = StatusTramitacao.objects.filter(
                    id=request.POST['status']).first()
                unidade_destino = UnidadeTramitacao.objects.get(
                    id=request.POST['unidade_tramitacao_destino']
                )
                texto = request.POST['texto']
                data_tramitacao = request.POST['data_tramitacao']
                do_envia_email_tramitacao(
                    request, materia, status,
                    unidade_destino, texto, data_tramitacao)

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
            super(MasterDetailCrud.CreateView, self).__init__(**kwargs)

        def get_context_data(self, **kwargs):
            context = super(
                MasterDetailCrud.CreateView, self).get_context_data(**kwargs)
            return context

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = DocumentoAcessorioForm

        def __init__(self, **kwargs):
            super(MasterDetailCrud.UpdateView, self).__init__(**kwargs)

        def get_context_data(self, **kwargs):
            context = super(UpdateView, self).get_context_data(**kwargs)
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

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DespachoInicialForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = DespachoInicialForm


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


class MateriaAssuntoCrud(MasterDetailCrud):
    model = MateriaAssunto
    parent_field = 'materia'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['assunto', 'materia']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = MateriaAssuntoForm

        def get_initial(self):
            self.initial['materia'] = self.kwargs['pk']
            return self.initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = MateriaAssuntoForm

        def get_initial(self):
            self.initial['materia'] = self.get_object().materia
            self.initial['assunto'] = self.get_object().assunto
            return self.initial


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

    class DeleteView(Crud.DeleteView):

        def get_success_url(self):
            return self.search_url

    class DetailView(Crud.DetailView):

        @property
        def layout_key(self):
            return 'MateriaLegislativaDetail'

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
    permission_required = ('materia.add_documentoacessorio', )

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


class AcompanhamentoConfirmarView(TemplateView):

    def get_redirect_url(self, email):
        msg = _('Esta matéria está sendo acompanhada pelo e-mail: %s') % (
            email)
        messages.add_message(self.request, messages.SUCCESS, msg)
        return reverse('sapl.materia:materialegislativa_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')

        try:
            acompanhar = AcompanhamentoMateria.objects.get(
                materia_id=materia_id,
                hash=hash_txt)
        except ObjectDoesNotExist:
            raise Http404()
        # except MultipleObjectsReturned:
        # A melhor solução deve ser permitir que a exceção
        # (MultipleObjectsReturned) seja lançada e vá para o log,
        # pois só poderá ser causada por um erro de desenvolvimente

        acompanhar.confirmado = True
        acompanhar.save()

        return HttpResponseRedirect(self.get_redirect_url(acompanhar.email))


class AcompanhamentoExcluirView(TemplateView):

    def get_success_url(self):
        return reverse('sapl.materia:materialegislativa_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')

        try:
            AcompanhamentoMateria.objects.get(materia_id=materia_id,
                                              hash=hash_txt).delete()
        except ObjectDoesNotExist:
            pass

        return HttpResponseRedirect(self.get_success_url())


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

        if 'o' in self.request.GET and not self.request.GET['o']:
            qs = qs.order_by('-ano', 'tipo__sigla', '-numero')

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

            acompanhar = AcompanhamentoMateria.objects.get_or_create(
                materia=materia,
                email=form.data['email'])

            # Se o segundo elemento do retorno do get_or_create for True
            # quer dizer que o elemento não existia
            if acompanhar[1]:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.usuario = usuario.username
                acompanhar.confirmado = False
                acompanhar.save()
                do_envia_email_confirmacao(request, materia, email)
                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                         de mensagens e clique no link que nós enviamos para \
                         confirmar o acompanhamento desta matéria.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Caso esse Acompanhamento já exista
            # avisa ao usuário que essa matéria já está sendo acompanhada
            else:
                msg = _('Este e-mail já está acompanhando essa matéria.')
                messages.add_message(request, messages.INFO, msg)

                return self.render_to_response(
                    {'form': form,
                     'materia': materia,
                     'error': _('Essa matéria já está\
                     sendo acompanhada por este e-mail.')})
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'form': form,
                 'materia': materia})

    def get_success_url(self):
        return reverse('sapl.materia:materialegislativa_detail',
                       kwargs={'pk': self.kwargs['pk']})


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
    materia_url = reverse('sapl.materia:materialegislativa_detail',
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


def criar_email_tramitacao(
        request, casa_legislativa, materia, status,
        unidade_destino, texto, data_tramitacao, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not materia:
        raise ValueError("Matéria é obrigatória")

    # FIXME i18n
    casa_nome = (casa_legislativa.nome + ' de ' +
                 casa_legislativa.municipio + '-' +
                 casa_legislativa.uf)

    base_url = get_base_url(request)
    url_materia = reverse('sapl.materia:tramitacao_list',
                          kwargs={'pk': materia.id})
    url_excluir = reverse('sapl.materia:acompanhar_excluir',
                          kwargs={'pk': materia.id})

    autores = []
    for autoria in materia.autoria_set.all():
        autores.append(autoria.autor.nome)

    tramitacao = materia.tramitacao_set.last()

    templates = load_email_templates(['email/tramitacao.txt',
                                      'email/tramitacao.html'],
                                     {"casa_legislativa": casa_nome,
                                      "data_registro": datetime.now().strftime(
                                          "%d/%m/%Y"),
                                      "cod_materia": materia.id,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_materia": materia.ementa,
                                      "autoria": autores,
                                      "data": data_tramitacao,
                                      "status": status,
                                      "localizacao": unidade_destino,
                                      "texto_acao": texto,
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

    sender = EMAIL_SEND_USER
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


def do_envia_email_tramitacao(
        request, materia, status, unidade_destino, texto, data_tramitacao):
    #
    # Envia email de tramitacao para usuarios cadastrados
    #
    destinatarios = AcompanhamentoMateria.objects.filter(materia=materia,
                                                         confirmado=True)
    casa = CasaLegislativa.objects.first()

    sender = EMAIL_SEND_USER
    # FIXME i18n
    subject = "[SAPL] " + str(materia) + \
              " - Acompanhamento de Materia Legislativa"
    messages = []
    recipients = []
    for destinatario in destinatarios:
        email_texts = criar_email_tramitacao(request,
                                             casa,
                                             materia,
                                             status,
                                             unidade_destino,
                                             texto,
                                             data_tramitacao,
                                             destinatario.hash,)
        recipients.append(destinatario.email)
        messages.append({
            'recipient': destinatario.email,
            'subject': subject,
            'txt_message': email_texts[0],
            'html_message': email_texts[1],
        })
    enviar_emails(sender, recipients, messages)


class DocumentoAcessorioEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = AcessorioEmLoteFilterSet
    template_name = 'materia/em_lote/acessorio.html'
    permission_required = ('materia.add_documentoacessorio',)

    def get_context_data(self, **kwargs):
        context = super(DocumentoAcessorioEmLoteView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Documentos Acessórios em Lote')
        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        qr = self.request.GET.copy()
        context['tipos_docs'] = TipoDocumento.objects.all()
        context['object_list'] = context['object_list'].order_by(
            'ano', 'numero')
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
            doc = DocumentoAcessorio()
            doc.materia_id = materia_id
            doc.tipo = tipo
            doc.arquivo = request.FILES['arquivo']
            doc.nome = request.POST['nome']
            doc.data = datetime.strptime(request.POST['data'], "%d/%m/%Y")
            doc.autor = request.POST['autor']
            doc.ementa = request.POST['ementa']
            doc.save()
        msg = _('Documento(s) criado(s).')
        messages.add_message(request, messages.SUCCESS, msg)
        return self.get(request, self.kwargs)


class PrimeiraTramitacaoEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = PrimeiraTramitacaoEmLoteFilterSet
    template_name = 'materia/em_lote/tramitacao.html'
    permission_required = ('materia.add_tramitacao', )

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

        context['object_list'] = context['object_list'].order_by(
            'ano', 'numero')

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

        # issue https://github.com/interlegis/sapl/issues/1123
        # TODO: usar Form
        urgente = request.POST['urgente'] == 'True'

        for materia_id in marcadas:
            t = Tramitacao(
                materia_id=materia_id,
                data_tramitacao=datetime.strptime(
                    request.POST['data_tramitacao'], "%d/%m/%Y"),
                data_encaminhamento=data_encaminhamento,
                data_fim_prazo=data_fim_prazo,
                unidade_tramitacao_local_id=request.POST[
                    'unidade_tramitacao_local'],
                unidade_tramitacao_destino_id=request.POST[
                    'unidade_tramitacao_destino'],
                urgente=urgente,
                status_id=request.POST['status'],
                turno=request.POST['turno'],
                texto=request.POST['texto']
            )
            t.save()
        msg = _('Tramitação completa.')
        messages.add_message(request, messages.SUCCESS, msg)
        return self.get(request, self.kwargs)


class TramitacaoEmLoteView(PrimeiraTramitacaoEmLoteView):
    filterset_class = TramitacaoEmLoteFilterSet

    def get_context_data(self, **kwargs):
        context = super(TramitacaoEmLoteView,
                        self).get_context_data(**kwargs)

        qr = self.request.GET.copy()

        if ('tramitacao__status' in qr and
                'tramitacao__unidade_tramitacao_destino' in qr and
                qr['tramitacao__status'] and
                qr['tramitacao__unidade_tramitacao_destino']
                ):
            lista = filtra_tramitacao_destino_and_status(
                qr['tramitacao__status'],
                qr['tramitacao__unidade_tramitacao_destino'])
            context['object_list'] = context['object_list'].filter(
                id__in=lista).distinct()

        return context
