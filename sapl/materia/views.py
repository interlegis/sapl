from datetime import datetime
from random import choice
from string import ascii_letters, digits

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.template import Context, loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (CreateView, DetailView, ListView,
                                  TemplateView, UpdateView)
from django_filters.views import FilterView

from sapl.base.models import CasaLegislativa
from sapl.compilacao.views import IntegracaoTaView
from sapl.crispy_layout_mixin import SaplFormLayout, form_actions, to_row
from sapl.crud.base import (Crud, CrudBaseMixin, CrudCreateView,
                            CrudDeleteView, CrudDetailView, CrudListView,
                            CrudUpdateView, make_pagination)
from sapl.crud.masterdetail import MasterDetailCrud
from sapl.norma.models import LegislacaoCitada
from sapl.utils import (autor_label, autor_modal, gerar_hash_arquivo,
                        get_base_url, permissao_tb_aux, permissoes_autor,
                        permissoes_materia)

from .forms import (AcompanhamentoMateriaForm, AnexadaForm, AutorForm,
                    AutoriaForm, ConfirmarProposicaoForm, DespachoInicialForm,
                    DocumentoAcessorioForm, LegislacaoCitadaForm,
                    MateriaLegislativaFilterSet, NumeracaoForm, ProposicaoForm,
                    ReceberProposicaoForm, RelatoriaForm, TramitacaoForm,
                    UnidadeTramitacaoForm, filtra_tramitacao_destino,
                    filtra_tramitacao_destino_and_status,
                    filtra_tramitacao_status)
from .models import (AcompanhamentoMateria, Anexada, Autor, Autoria,
                     DespachoInicial, DocumentoAcessorio, MateriaLegislativa,
                     Numeracao, Orgao, Origem, Proposicao, RegimeTramitacao,
                     Relatoria, StatusTramitacao, TipoAutor, TipoDocumento,
                     TipoFimRelatoria, TipoMateriaLegislativa, TipoProposicao,
                     Tramitacao, UnidadeTramitacao)

AnexadaCrud = Crud.build(Anexada, '')


class OrigemCrud(Crud):
    model = Origem
    help_path = 'origem'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class TipoMateriaCrud(Crud):
    model = TipoMateriaLegislativa
    help_path = 'tipo_materia_legislativa'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class RegimeTramitacaoCrud(Crud):
    model = RegimeTramitacao
    help_path = 'regime_tramitacao'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class TipoDocumentoCrud(Crud):
    model = TipoDocumento
    help_path = 'tipo_documento'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class TipoFimRelatoriaCrud(Crud):
    model = TipoFimRelatoria
    help_path = 'fim_relatoria'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class TipoAutorCrud(Crud):
    model = TipoAutor
    help_path = 'tipo_autor'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class AutorCrud(Crud):
    model = Autor
    help_path = 'autor'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        list_field_names = ['tipo', 'nome',
                            'username', 'cargo']

        def has_permission(self):
            return permissao_tb_aux(self)

    class CreateView(CrudCreateView):
        form_class = AutorForm
        layout_key = 'AutorCreate'

        def get_success_url(self):
            pk_autor = Autor.objects.get(
                email=self.request.POST.get('email')).id
            kwargs = {}
            user = User.objects.get(email=self.request.POST.get('email'))
            kwargs['token'] = default_token_generator.make_token(user)
            kwargs['uidb64'] = urlsafe_base64_encode(force_bytes(user.pk))
            assunto = "SAPL - Confirmação de Conta"
            full_url = self.request.get_raw_uri()
            url_base = full_url[:full_url.find('sistema') - 1]

            mensagem = ("Este e-mail foi utilizado para fazer cadastro no " +
                        "SAPL com o perfil de Autor. Agora você pode " +
                        "criar/editar/enviar Proposições.\n" +
                        "Seu nome de usuário é: " +
                        self.request.POST['username'] + "\n"
                        "Caso você não tenha feito este cadastro, por favor " +
                        "ignore esta mensagem. Caso tenha, clique " +
                        "no link abaixo\n" + url_base +
                        reverse('sapl.materia:confirmar_email', kwargs=kwargs))
            remetente = settings.EMAIL_SEND_USER
            destinatario = [self.request.POST.get('email')]
            send_mail(assunto, mensagem, remetente, destinatario,
                      fail_silently=False)
            return reverse('sapl.materia:autor_detail',
                           kwargs={'pk': pk_autor})


class ConfirmarEmailView(TemplateView):
    template_name = "confirma_email.html"

    def get(self, request, *args, **kwargs):
        uid = urlsafe_base64_decode(self.kwargs['uidb64'])
        user = User.objects.get(id=uid)
        user.is_active = True
        user.save()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class OrgaoCrud(Crud):
    model = Orgao
    help_path = 'orgao'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


class TipoProposicaoCrud(Crud):
    model = TipoProposicao
    help_path = 'tipo_proposicao'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        def has_permission(self):
            return permissao_tb_aux(self)


class StatusTramitacaoCrud(Crud):
    model = StatusTramitacao
    help_path = 'status_tramitacao'

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):

        def has_permission(self):
            return permissao_tb_aux(self)


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


class UnidadeTramitacaoCrud(Crud):
    model = UnidadeTramitacao
    help_path = 'unidade_tramitacao'

    class CreateView(PermissionRequiredMixin, CrudCreateView):
        permission_required = permissoes_materia()
        form_class = UnidadeTramitacaoForm

    class UpdateView(PermissionRequiredMixin, CrudUpdateView):
        permission_required = permissoes_materia()
        form_class = UnidadeTramitacaoForm

    class DeleteView(PermissionRequiredMixin, CrudDeleteView):
        permission_required = permissoes_materia()


class ProposicaoDevolvida(ListView):
    template_name = 'materia/prop_devolvidas_list.html'
    model = Proposicao
    ordering = ['data_envio']
    paginate_by = 10

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


class ProposicaoPendente(ListView):
    template_name = 'materia/prop_pendentes_list.html'
    model = Proposicao
    ordering = ['data_envio', 'autor', 'tipo', 'descricao']
    paginate_by = 10

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


class ProposicaoRecebida(ListView):
    template_name = 'materia/prop_recebidas_list.html'
    model = Proposicao
    ordering = ['data_envio']
    paginate_by = 10

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


class ReceberProposicao(CreateView):
    template_name = "materia/receber_proposicao.html"
    form_class = ReceberProposicaoForm

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


class ConfirmarProposicao(CreateView):
    template_name = "materia/confirmar_proposicao.html"
    form_class = ConfirmarProposicaoForm

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

    class BaseMixin(CrudBaseMixin):
        list_field_names = ['data_envio', 'descricao',
                            'tipo', 'data_recebimento']

    class CreateView(PermissionRequiredMixin, CrudCreateView):
        form_class = ProposicaoForm
        permission_required = {'materia.add_proposicao'}

        @property
        def layout_key(self):
            return 'ProposicaoCreate'

        def get_initial(self):
            try:
                autor_id = Autor.objects.get(id=self.request.user.id).id
            except MultipleObjectsReturned:
                msg = _('Este usuário está relacionado a mais de um autor. ' +
                        'Operação cancelada')
                messages.add_message(self.request, messages.ERROR, msg)
                return redirect(self.get_success_url())
            else:
                return {'autor': autor_id}

    class UpdateView(PermissionRequiredMixin, CrudUpdateView):
        form_class = ProposicaoForm
        permission_required = permissoes_autor()

        @property
        def layout_key(self):
            return 'ProposicaoCreate'

        def has_permission(self):
            perms = self.get_permission_required()
            if self.request.user.has_perms(perms):
                if (Proposicao.objects.filter(
                   id=self.kwargs['pk'],
                   autor__user_id=self.request.user.id).exists()):
                    proposicao = Proposicao.objects.get(
                        id=self.kwargs['pk'],
                        autor__user_id=self.request.user.id)
                    if not proposicao.data_recebimento:
                        return True
                    else:
                        msg = _('Essa proposição já foi recebida. ' +
                                'Não pode mais ser editada')
                        messages.add_message(self.request, messages.ERROR, msg)
                        return False
            else:
                return False

    class DetailView(PermissionRequiredMixin, CrudDetailView):
        permission_required = permissoes_autor()

        def get_context_data(self, **kwargs):
            context = super(DetailView, self).get_context_data(**kwargs)
            if self.object.materia:
                context['form'].fields['tipo_materia'].initial = (
                    self.object.materia.tipo.id)
                context['form'].fields['numero_materia'].initial = (
                    self.object.materia.numero)
                context['form'].fields['ano_materia'].initial = (
                    self.object.materia.ano)
            return context

        @property
        def layout_key(self):
            return 'ProposicaoCreate'

        def has_permission(self):
            perms = self.get_permission_required()
            if self.request.user.has_perms(perms):
                if (Proposicao.objects.filter(
                   id=self.kwargs['pk'],
                   autor__user_id=self.request.user.id).exists()):
                    return True
                else:
                    return False
            else:
                return False

    class ListView(PermissionRequiredMixin, CrudListView):
        ordering = ['-data_envio', 'descricao']
        permission_required = permissoes_autor()

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
            lista = Proposicao.objects.filter(
                autor__user_id=self.request.user.id)
            return lista

    class DeleteView(PermissionRequiredMixin, CrudDeleteView):
        permission_required = permissoes_materia()

        def delete(self, request, *args, **kwargs):
            proposicao = Proposicao.objects.get(id=self.kwargs['pk'])

            if not proposicao.data_envio:
                proposicao.delete()
                return HttpResponseRedirect(
                    reverse('sapl.materia:proposicao_list'))
            else:
                proposicao.data_envio = None
                proposicao.save()
                return HttpResponseRedirect(
                    reverse('sapl.materia:proposicao_detail',
                            kwargs={'pk': proposicao.pk}))


class ReciboProposicaoView(TemplateView):
    template_name = "materia/recibo_proposicao.html"

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

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        permission_required = permissoes_materia()
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

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        permission_required = permissoes_materia()
        form_class = RelatoriaForm

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()


class TramitacaoCrud(MasterDetailCrud):
    model = Tramitacao
    parent_field = 'materia'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = TramitacaoForm
        permission_required = permissoes_materia()

        def post(self, request, *args, **kwargs):
            materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
            do_envia_email_tramitacao(request, materia)
            return super(CreateView, self).post(request, *args, **kwargs)

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = TramitacaoForm
        permission_required = permissoes_materia()

        def post(self, request, *args, **kwargs):
            materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
            do_envia_email_tramitacao(request, materia)
            return super(UpdateView, self).post(request, *args, **kwargs)

    class ListView(MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao')

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()

        def delete(self, request, *args, **kwargs):
            tramitacao = Tramitacao.objects.get(id=self.kwargs['pk'])
            materia = MateriaLegislativa.objects.get(id=tramitacao.materia.id)
            url = reverse('sapl.materia:tramitacao_list',
                          kwargs={'pk': tramitacao.materia.id})

            if tramitacao.pk != materia.tramitacao_set.last().pk:
                msg = _('Somente a útlima tramitação pode ser deletada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(url)
            else:
                tramitacao.delete()
                return HttpResponseRedirect(url)


def montar_row_autor():
    autor_row = to_row(
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

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'tipo', 'data', 'autor', 'arquivo']

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = DocumentoAcessorioForm
        permission_required = permissoes_materia()

        def __init__(self, *args, **kwargs):
            montar_helper_documento_acessorio(self)
            super(CreateView, self).__init__(*args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super(CreateView, self).get_context_data(**kwargs)
            context['helper'] = self.helper
            return context

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = DocumentoAcessorioForm
        permission_required = permissoes_materia()

        def __init__(self, *args, **kwargs):
            montar_helper_documento_acessorio(self)
            super(UpdateView, self).__init__(*args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super(UpdateView, self).get_context_data(**kwargs)
            context['helper'] = self.helper
            return context

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()


class AutoriaCrud(MasterDetailCrud):
    model = Autoria
    parent_field = 'materia'
    help_path = ''

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = AutoriaForm
        permission_required = permissoes_materia()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = AutoriaForm
        permission_required = permissoes_materia()

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()


class DespachoInicialCrud(MasterDetailCrud):
    model = DespachoInicial
    parent_field = 'materia'
    help_path = ''

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = DespachoInicialForm
        permission_required = permissoes_materia()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = DespachoInicialForm
        permission_required = permissoes_materia()

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()


class LegislacaoCitadaCrud(MasterDetailCrud):
    model = LegislacaoCitada
    parent_field = 'materia'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['norma', 'disposicoes']

        def resolve_url(self, suffix, args=None):
            namespace = 'sapl.materia'
            return reverse('%s:%s' % (namespace, self.url_name(suffix)),
                           args=args)

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = LegislacaoCitadaForm
        permission_required = permissoes_materia()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = LegislacaoCitadaForm
        permission_required = permissoes_materia()

        def get_initial(self):
            self.initial['tipo'] = self.object.norma.tipo.id
            self.initial['numero'] = self.object.norma.numero
            self.initial['ano'] = self.object.norma.ano
            return self.initial

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'LegislacaoCitadaDetail'


class NumeracaoCrud(MasterDetailCrud):
    model = Numeracao
    parent_field = 'materia'
    help_path = ''

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = NumeracaoForm
        permission_required = permissoes_materia()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = NumeracaoForm
        permission_required = permissoes_materia()

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()


class AnexadaCrud(MasterDetailCrud):
    model = Anexada
    parent_field = 'materia_principal'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['materia_anexada', 'data_anexacao']

    class CreateView(PermissionRequiredMixin, MasterDetailCrud.CreateView):
        form_class = AnexadaForm
        permission_required = permissoes_materia()

    class UpdateView(PermissionRequiredMixin, MasterDetailCrud.UpdateView):
        form_class = AnexadaForm
        permission_required = permissoes_materia()

        def get_initial(self):
            self.initial['tipo'] = self.object.materia_anexada.tipo.id
            self.initial['numero'] = self.object.materia_anexada.numero
            self.initial['ano'] = self.object.materia_anexada.ano

            return self.initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'AnexadaDetail'

    class DeleteView(PermissionRequiredMixin, MasterDetailCrud.DeleteView):
        permission_required = permissoes_materia()


class MateriaLegislativaCrud(Crud):
    model = MateriaLegislativa
    help_path = 'materia_legislativa'

    class BaseMixin(CrudBaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data_apresentacao']

    class CreateView(PermissionRequiredMixin, CrudCreateView):
        permission_required = permissoes_materia()

    class UpdateView(PermissionRequiredMixin, CrudUpdateView):
        permission_required = permissoes_materia()

    class DeleteView(PermissionRequiredMixin, CrudDeleteView):
        permission_required = permissoes_materia()


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

        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        self.filterset.form.fields['o'].label = _('Ordenação')

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        return context


class MateriaTaView(IntegracaoTaView):
    model = MateriaLegislativa
    model_type_foreignkey = TipoMateriaLegislativa


class ProposicaoTaView(IntegracaoTaView):
    model = Proposicao
    model_type_foreignkey = TipoProposicao


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
