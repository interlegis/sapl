from datetime import datetime
import logging
from random import choice
import re
from string import ascii_letters, digits

from braces.views import FormValidMessageMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Max, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.edit import FormView
from django_filters.views import FilterView

import sapl
from sapl.base.email_utils import do_envia_email_confirmacao
from sapl.base.models import Autor, CasaLegislativa, AppConfig
from sapl.comissoes.models import Comissao
from sapl.crud.base import (Crud, CrudAux, MasterDetailCrud, make_pagination,
                            RP_LIST, RP_DETAIL)
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa, UnidadeTramitacao
from sapl.materia.views import gerar_pdf_impressos
from sapl.parlamentares.models import Legislatura, Parlamentar
from sapl.protocoloadm.forms import VinculoDocAdminMateriaForm
from sapl.protocoloadm.models import Protocolo, DocumentoAdministrativo,\
    VinculoDocAdminMateria
from sapl.relatorios.views import relatorio_doc_administrativos
from sapl.utils import (create_barcode, get_base_url, get_client_ip,
                        get_mime_type_from_file_extension, lista_anexados,
                        show_results_filter_set, mail_service_configured, from_date_to_datetime_utc,
                        google_recaptcha_configured)

from .forms import (AcompanhamentoDocumentoForm, AnexadoEmLoteFilterSet, AnexadoForm,
                    AnularProtocoloAdmForm, compara_tramitacoes_doc,
                    DesvincularDocumentoForm, DesvincularMateriaForm,
                    DocumentoAcessorioAdministrativoForm, DocumentoAdministrativoFilterSet,
                    DocumentoAdministrativoForm, FichaPesquisaAdmForm, FichaSelecionaAdmForm,
                    filtra_tramitacao_adm_destino, filtra_tramitacao_adm_destino_and_status,
                    filtra_tramitacao_adm_status,  PrimeiraTramitacaoEmLoteAdmFilterSet,
                    ProtocoloDocumentoForm, ProtocoloFilterSet, ProtocoloMateriaForm,
                    TramitacaoAdmEditForm, TramitacaoAdmForm, TramitacaoEmLoteAdmForm,
                    TramitacaoEmLoteAdmFilterSet)
from .models import (Anexado, AcompanhamentoDocumento, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)


TipoDocumentoAdministrativoCrud = CrudAux.build(
    TipoDocumentoAdministrativo, '')


# ProtocoloDocumentoCrud = Crud.build(Protocolo, '')
# FIXME precisa de uma chave diferente para o layout
# ProtocoloMateriaCrud = Crud.build(Protocolo, '')

@permission_required('protocoloadm.add_protocolo')
def recuperar_materia_protocolo(request):
    tipo = request.GET.get('tipo')
    ano = request.GET.get('ano')
    numero = request.GET.get('numero')
    logger = logging.getLogger(__name__)
    username = request.user.username
    try:
        logger.debug("user=" + username +
                     ". Tentando obter matéria com tipo={}, ano={} e numero={}.".format(tipo, ano, numero))
        materia = MateriaLegislativa.objects.get(
            tipo=tipo, ano=ano, numero=numero)
        autoria = materia.autoria_set.first()
        content = {'ementa': materia.ementa.strip(),
                   'ano': materia.ano, 'numero': materia.numero}
        if autoria:
            content.update({'autor': autoria.autor.pk,
                            'tipo_autor': autoria.autor.tipo.pk})
        response = JsonResponse(content)
    except Exception as e:
        logger.error("user=" + username + ". " + str(e))
        response = JsonResponse({'error': e})
    return response


def doc_texto_integral(request, pk):
    can_see = True

    if not request.user.is_authenticated:
        app_config = AppConfig.objects.last()
        if app_config and app_config.documentos_administrativos == 'R':
            can_see = False

    if can_see:
        documento = DocumentoAdministrativo.objects.get(pk=pk)
        if documento.texto_integral:
            arquivo = documento.texto_integral

            mime = get_mime_type_from_file_extension(arquivo.name)

            with open(arquivo.path, 'rb') as f:
                data = f.read()

            response = HttpResponse(data, content_type='%s' % mime)
            response['Content-Disposition'] = (
                'inline; filename="%s"' % arquivo.name.split('/')[-1])
            return response
    raise Http404


class AcompanhamentoConfirmarView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_redirect_url(self, email):
        username = self.request.user.username
        self.logger.info(
            'user=' + username + '. Este documento está sendo acompanhado pelo e-mail: {}'.format(email))
        msg = _('Este documento está sendo acompanhado pelo e-mail: %s') % (
            email)
        messages.add_message(self.request, messages.SUCCESS, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):

        documento_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = request.user.username

        try:
            self.logger.debug("user=" + username + ". Tentando obter objeto AcompanhamentoDocumento com documento_id={} e hash={}"
                              .format(documento_id, hash_txt))
            acompanhar = AcompanhamentoDocumento.objects.get(
                documento_id=documento_id,
                hash=hash_txt)
        except ObjectDoesNotExist as e:
            self.logger.error("user=" + username + ". " + str(e))
            raise Http404()
        # except MultipleObjectsReturned:
        # A melhor solução deve ser permitir que a exceção
        # (MultipleObjectsReturned) seja lançada e vá para o log,
        # pois só poderá ser causada por um erro de desenvolvimente

        acompanhar.confirmado = True
        acompanhar.save()

        return HttpResponseRedirect(self.get_redirect_url(acompanhar.email))


class AcompanhamentoExcluirView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_success_url(self):
        username = self.request.user.username
        self.logger.info(
            "user=" + username + ". Você parou de acompanhar este Documento (pk={}).".format(self.kwargs['pk']))
        msg = _('Você parou de acompanhar este Documento.')
        messages.add_message(self.request, messages.INFO, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        documento_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = request.user.username
        try:
            self.logger.debug("user=" + username + ". Tentando obter AcompanhamentoDocumento com documento_id={} e hash={}."
                              .format(documento_id, hash_txt))
            AcompanhamentoDocumento.objects.get(documento_id=documento_id,
                                                hash=hash_txt).delete()
        except ObjectDoesNotExist:
            self.logger.error("user=" + username + ". AcompanhamentoDocumento com documento_id={} e hash={} não encontrado."
                              .format(documento_id, hash_txt))

        return HttpResponseRedirect(self.get_success_url())


class AcompanhamentoDocumentoView(CreateView):
    template_name = "protocoloadm/acompanhamento_documento.html"

    logger = logging.getLogger(__name__)

    def get_random_chars(self):
        s = ascii_letters + digits
        return ''.join(choice(s) for i in range(choice([6, 7])))

    def get(self, request, *args, **kwargs):
        if not mail_service_configured():
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Documentos não foi configurado'))
            return redirect('/')

        if not google_recaptcha_configured():
            self.logger.warning(_('Google Recaptcha não configurado!'))
            messages.error(request, _('Google Recaptcha não configurado!'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        pk = self.kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)

        return self.render_to_response(
            {'form': AcompanhamentoDocumentoForm(),
             'documento': documento})

    def post(self, request, *args, **kwargs):
        if not mail_service_configured():
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Documentos não foi configurado'))
            return redirect('/')

        if not google_recaptcha_configured():
            self.logger.warning(_('Google Recaptcha não configurado!'))
            messages.error(request, _('Google Recaptcha não configurado!'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        form = AcompanhamentoDocumentoForm(request.POST)
        pk = self.kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)

        if form.is_valid():
            email = form.cleaned_data['email']
            usuario = request.user

            hash_txt = self.get_random_chars()

            acompanhar = AcompanhamentoDocumento.objects.get_or_create(
                documento=documento,
                email=form.data['email'])

            # Se o segundo elemento do retorno do get_or_create for True
            # quer dizer que o elemento não existia
            if acompanhar[1]:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.usuario = usuario.username
                acompanhar.confirmado = False
                acompanhar.save()

                base_url = get_base_url(request)

                destinatario = AcompanhamentoDocumento.objects.get(
                    documento=documento,
                    email=email,
                    confirmado=False)
                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "documento",
                                           documento,
                                           destinatario)
                self.logger.info('user={}. Foi enviado um e-mail de confirmação. Confira sua caixa '
                                 'de mensagens e clique no link que nós enviamos para '
                                 'confirmar o acompanhamento deste documento.'.format(usuario.username))
                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                         de mensagens e clique no link que nós enviamos para \
                         confirmar o acompanhamento deste documento.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Se o elemento existir e o email não foi confirmado:
            # gerar novo hash e reenviar mensagem de email
            elif not acompanhar[0].confirmado:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.save()

                base_url = get_base_url(request)

                destinatario = AcompanhamentoDocumento.objects.get(
                    documento=documento,
                    email=email,
                    confirmado=False
                )

                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "documento",
                                           documento,
                                           destinatario)

                self.logger.info('user={}. Foi enviado um e-mail de confirmação. Confira sua caixa \
                                  de mensagens e clique no link que nós enviamos para \
                                  confirmar o acompanhamento deste documento.'.format(usuario.username))

                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                        de mensagens e clique no link que nós enviamos para \
                        confirmar o acompanhamento deste documento.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Caso esse Acompanhamento já exista
            # avisa ao usuário que esse documento já está sendo acompanhado
            else:
                self.logger.info('user=' + request.user.username +
                                 '. Este e-mail já está acompanhando esse documento (pk={}).'.format(pk))
                msg = _('Este e-mail já está acompanhando esse documento.')
                messages.add_message(request, messages.ERROR, msg)

                return self.render_to_response(
                    {'form': form,
                     'documento': documento,
                     })
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'form': form,
                 'documento': documento})

    def get_success_url(self):
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})


class DocumentoAdministrativoMixin:

    def has_permission(self):
        app_config = AppConfig.objects.last()
        if app_config and app_config.documentos_administrativos == 'O':
            return True

        return super().has_permission()


class DocumentoAdministrativoCrud(Crud):
    model = DocumentoAdministrativo
    help_topic = 'numeracao_docsacess'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data',
                            'protocolo__numero', 'assunto',
                            'interessado', 'tramitacao', 'texto_integral']

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesq_doc_adm'))

        list_url = ''

    class ListView(RedirectView, DocumentoAdministrativoMixin, Crud.ListView):

        def get_redirect_url(self, *args, **kwargs):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesq_doc_adm'))

    class CreateView(Crud.CreateView):
        form_class = DocumentoAdministrativoForm
        layout_key = None

        def get_initial(self):
            initial = super().get_initial()

            initial['user'] = self.request.user
            initial['ip'] = get_client_ip(self.request)

            tz = timezone.get_current_timezone()
            initial['ultima_edicao'] = tz.localize(datetime.now())

            return initial

        @property
        def cancel_url(self):
            return self.search_url

        def form_valid(self, form):
            form.instance.complemento = re.sub(
                '\s+', '', form.instance.complemento).upper()
            return super().form_valid(form)

    class UpdateView(Crud.UpdateView):
        form_class = DocumentoAdministrativoForm
        layout_key = None

        def form_valid(self, form):
            dict_objeto_antigo = DocumentoAdministrativo.objects.get(
                pk=self.kwargs['pk']
            ).__dict__

            self.object = form.save()
            dict_objeto_novo = self.object.__dict__

            atributos = [
                'tipo_id', 'ano', 'numero', 'data', 'protocolo_id', 'assunto',
                'interessado', 'tramitacao', 'restrito', 'texto_integral', 'numero_externo',
                'dias_prazo', 'data_fim_prazo', 'observacao'
            ]

            for atributo in atributos:
                if dict_objeto_antigo[atributo] != dict_objeto_novo[atributo]:
                    self.object.user = self.request.user
                    self.object.ip = get_client_ip(self.request)

                    tz = timezone.get_current_timezone()
                    self.object.ultima_edicao = tz.localize(datetime.now())

                    self.object.save()
                    break

            form.instance.complemento = re.sub(
                '\s+', '', form.instance.complemento).upper()

            return super().form_valid(form)

        def get_initial(self):
            if self.object.protocolo:
                p = self.object.protocolo
                return {'ano_protocolo': p.ano,
                        'numero_protocolo': p.numero}

    class DetailView(DocumentoAdministrativoMixin, Crud.DetailView):

        def get(self, *args, **kwargs):
            pk = self.kwargs['pk']
            documento = DocumentoAdministrativo.objects.get(id=pk)
            if documento.restrito and self.request.user.is_anonymous:
                return redirect('/')
            return super(Crud.DetailView, self).get(args, kwargs)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            context['user'] = self.request.user
            context['documentoadministrativo'] = DocumentoAdministrativo.objects.get(
                pk=self.kwargs['pk']
            )

            return context

        def urlize(self, obj, fieldname):
            a = '<a href="%s">%s</a>' % (
                reverse(
                    'sapl.protocoloadm:doc_texto_integral',
                    kwargs={'pk': obj.pk}),
                obj.texto_integral.name.split('/')[-1])
            return obj.texto_integral.field.verbose_name, a

    class DeleteView(Crud.DeleteView):

        def get_success_url(self):
            return self.search_url


class StatusTramitacaoAdministrativoCrud(CrudAux):
    model = StatusTramitacaoAdministrativo
    help_topic = 'status_tramitacao'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['sigla', 'indicador', 'descricao']

    class ListView(CrudAux.ListView):
        ordering = 'sigla'


class ProtocoloPesquisaView(PermissionRequiredMixin, FilterView):
    model = Protocolo
    filterset_class = ProtocoloFilterSet
    paginate_by = 10
    permission_required = ('protocoloadm.list_protocolo',)

    def get_filterset_kwargs(self, filterset_class):
        super(ProtocoloPesquisaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset().order_by('ano', 'numero').distinct()

        if 'o' in self.request.GET and not self.request.GET['o']:
            qs = qs.order_by('-ano', '-numero')

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ProtocoloPesquisaView,
                        self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['title'] = _('Protocolo')

        return context

    def get(self, request, *args, **kwargs):
        super(ProtocoloPesquisaView, self).get(request)

        # Se a pesquisa estiver quebrando com a paginação
        # Olhe esta função abaixo
        # Provavelmente você criou um novo campo no Form/FilterSet
        # Então a ordem da URL está diferente
        data = self.filterset.data
        if data and data.get('numero') is not None:
            url = "&" + str(self.request.environ['QUERY_STRING'])
            if url.startswith("&page"):
                ponto_comeco = url.find('numero=') - 1
                url = url[ponto_comeco:]
        else:
            url = ''

        self.filterset.form.fields['o'].label = _('Ordenação')

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list,
                                        filter_url=url,
                                        numero_res=len(self.object_list)
                                        )

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)


class ProtocoloListView(PermissionRequiredMixin, ListView):
    template_name = 'protocoloadm/protocolo_list.html'
    context_object_name = 'protocolos'
    model = Protocolo
    paginate_by = 10
    permission_required = ('protocoloadm.list_protocolo',)

    def get_queryset(self):
        kwargs = self.request.session['kwargs']
        return Protocolo.objects.filter(
            **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProtocoloListView, self).get_context_data(
            **kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        return context


class AnularProtocoloAdmView(PermissionRequiredMixin, CreateView):
    template_name = 'protocoloadm/anular_protocoloadm.html'
    form_class = AnularProtocoloAdmForm
    form_valid_message = _('Protocolo anulado com sucesso!')
    permission_required = ('protocoloadm.action_anular_protocolo', )

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def get_initial(self):
        initial_data = {}
        initial_data['user_anulacao'] = self.request.user.username
        initial_data['ip_anulacao'] = get_client_ip(self.request)
        return initial_data

    def form_valid(self, form):
        protocolo = Protocolo.objects.get(numero=form.cleaned_data['numero'],
                                          ano=form.cleaned_data['ano'])
        protocolo.anulado = True
        protocolo.justificativa_anulacao = (
            form.cleaned_data['justificativa_anulacao'])
        protocolo.user_anulacao = form.cleaned_data['user_anulacao']
        protocolo.ip_anulacao = form.cleaned_data['ip_anulacao']
        protocolo.timestamp_anulacao = timezone.now()
        protocolo.save()
        return redirect(self.get_success_url())


class ProtocoloDocumentoView(PermissionRequiredMixin,
                             FormValidMessageMixin,
                             CreateView):

    logger = logging.getLogger(__name__)

    template_name = "protocoloadm/protocolar_documento.html"
    form_class = ProtocoloDocumentoForm
    form_valid_message = _('Protocolo cadastrado com sucesso!')
    permission_required = ('protocoloadm.add_protocolo', )

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.object.id})

    def get_initial(self):
        initial = super().get_initial()

        initial['user'] = self.request.user.username
        initial['user_data_hora_manual'] = self.request.user.username
        initial['ip_data_hora_manual'] = get_client_ip(self.request)
        initial['data'] = timezone.localdate(timezone.now())
        initial['hora'] = timezone.localtime(timezone.now())
        return initial

    @transaction.atomic
    def form_valid(self, form):
        protocolo = form.save(commit=False)
        username = self.request.user.username

        self.logger.debug("user=" + username +
                          ". Tentando obter sequência de numeração.")
        numeracao = AppConfig.objects.last(
        ).sequencia_numeracao_protocolo
        if not numeracao:
            self.logger.error("user=" + username + ". É preciso definir a sequencia de "
                              "numeração na tabelas auxiliares! ")
            msg = _('É preciso definir a sequencia de ' +
                    'numeração na tabelas auxiliares!')
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())

        if numeracao == 'A':
            numero_max = Protocolo.objects.filter(ano=timezone.now().year).aggregate(
                Max('numero')
            )['numero__max']
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year
            ).first()

            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim

            data_inicio_utc = from_date_to_datetime_utc(data_inicio)
            data_fim_utc = from_date_to_datetime_utc(data_fim)

            numero_max = Protocolo.objects.filter(
                Q(data__isnull=False, data__gte=data_inicio, data__lte=data_fim) | Q(
                    timestamp__isnull=False, timestamp__gte=data_inicio_utc,
                    timestamp__lte=data_fim_utc
                ) | Q(
                    timestamp_data_hora_manual__isnull=False,
                    timestamp_data_hora_manual__gte=data_inicio_utc,
                    timestamp_data_hora_manual__lte=data_fim_utc,
                )
            ).aggregate(Max('numero'))['numero__max']
        elif numeracao == 'U':
            numero_max = Protocolo.objects.all().aggregate(Max('numero'))[
                'numero__max']

        protocolo.tipo_processo = '0'  # TODO validar o significado
        protocolo.anulado = False

        inicio_numeracao = AppConfig.objects.first().inicio_numeracao_protocolo
        numero = int(numero_max) if numero_max else 0
        protocolo.numero = (
            (numero + 1) if numero and numero >= inicio_numeracao else inicio_numeracao
        )

        protocolo.ano = timezone.now().year
        protocolo.assunto_ementa = self.request.POST['assunto']
        protocolo.user = self.request.user

        if form.cleaned_data['data_hora_manual'] == 'True':
            protocolo.timestamp = None
            protocolo.user_data_hora_manual = username
            protocolo.ip_data_hora_manual = get_client_ip(self.request)
        else:
            protocolo.data = None
            protocolo.hora = None
            protocolo.user_data_hora_manual = ''
            protocolo.ip_data_hora_manual = ''

        protocolo.save()
        self.object = protocolo
        return redirect(self.get_success_url())


class CriarDocumentoProtocolo(PermissionRequiredMixin, CreateView):
    template_name = "protocoloadm/criar_documento.html"
    form_class = DocumentoAdministrativoForm
    permission_required = ('protocoloadm.add_documentoadministrativo',)

    def get_initial(self):
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        return self.criar_documento(protocolo)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.kwargs['pk']})

    def criar_documento(self, protocolo):
        curr_year = timezone.now().year

        numero_max = DocumentoAdministrativo.objects.filter(
            tipo=protocolo.tipo_documento, ano=curr_year
        ).aggregate(Max('numero'))['numero__max']

        doc = {}
        doc['tipo'] = protocolo.tipo_documento
        doc['ano'] = curr_year
        doc['data'] = timezone.now()
        doc['numero_protocolo'] = protocolo.numero
        doc['ano_protocolo'] = protocolo.ano
        doc['protocolo'] = protocolo.id
        doc['assunto'] = protocolo.assunto_ementa
        doc['interessado'] = protocolo.interessado
        doc['numero'] = numero_max + 1 if numero_max else 1
        doc['user'] = self.request.user
        doc['ip'] = get_client_ip(self.request)

        tz = timezone.get_current_timezone()
        doc['ultima_edicao'] = tz.localize(datetime.now())

        return doc


class ProtocoloMostrarView(PermissionRequiredMixin, TemplateView):
    logger = logging.getLogger(__name__)

    template_name = "protocoloadm/protocolo_mostrar.html"
    permission_required = ('protocoloadm.detail_protocolo', )

    def get_context_data(self, **kwargs):

        context = super(ProtocoloMostrarView, self).get_context_data(**kwargs)
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        username = self.request.user.username

        if protocolo.tipo_materia:
            self.logger.debug(
                "user=" + username +
                ". Tentando obter objeto MateriaLegislativa com numero_protocolo={} e ano={}."
                .format(protocolo.numero, protocolo.ano))
            materia = MateriaLegislativa.objects.filter(
                numero_protocolo=protocolo.numero, ano=protocolo.ano)
            context['materia'] = materia
            if len(materia) > 1:
                msg = _('Foi encontrada mais de uma matéria com o mesmo número de protocolo e ano.'
                        ' Isso é um erro de uso!'
                        ' Reporte isso ao suporte para que seja corrigido.')
                messages.add_message(self.request, messages.ERROR, msg)
                self.logger.error(
                    "user=" + username + ". Objeto MateriaLegislativa com numero_protocolo={} e ano={}"
                                         " encontrado mais de um registro."
                                         " Erro relatado ao usuário.".format(protocolo.numero, protocolo.ano))

        if protocolo.tipo_documento:
            context[
                'documentos'] = protocolo.documentoadministrativo_set\
                                         .all().order_by('-ano', '-numero')

        context['protocolo'] = protocolo
        return context


class ComprovanteProtocoloView(PermissionRequiredMixin, TemplateView):

    template_name = "protocoloadm/comprovante.html"
    permission_required = ('protocoloadm.detail_protocolo', )

    def get_context_data(self, **kwargs):
        context = super(ComprovanteProtocoloView, self).get_context_data(
            **kwargs)
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        # numero is string, padd with zeros left via .zfill()
        base64_data = create_barcode(str(protocolo.numero).zfill(6))
        barcode = 'data:image/png;base64,{0}'.format(base64_data)

        autenticacao = _("** NULO **")

        if not protocolo.anulado:
            if protocolo.timestamp:
                data = protocolo.timestamp.strftime("%Y/%m/%d")
            else:
                data = protocolo.data.strftime("%Y/%m/%d")

            # data is not i18n sensitive 'Y-m-d' is the right format.
            autenticacao = str(protocolo.tipo_processo) + \
                data + str(protocolo.numero).zfill(6)

        if protocolo.tipo_materia:
            materia = MateriaLegislativa.objects.filter(
                numero_protocolo=protocolo.numero,
                ano=protocolo.ano).first()
            if materia:
                context['materia'] = materia.numero

        context.update({"protocolo": protocolo,
                        "barcode": barcode,
                        "autenticacao": autenticacao})
        return context


class ProtocoloMateriaView(PermissionRequiredMixin, CreateView):

    logger = logging.getLogger(__name__)

    template_name = "protocoloadm/protocolar_materia.html"
    form_class = ProtocoloMateriaForm
    form_valid_message = _('Matéria cadastrada com sucesso!')
    permission_required = ('protocoloadm.add_protocolo',)

    def get_success_url(self, protocolo):
        return reverse('sapl.protocoloadm:materia_continuar', kwargs={
            'pk': protocolo.pk})

    def get_initial(self):
        initial = super().get_initial()

        initial['user'] = self.request.user.username
        initial['user_data_hora_manual'] = self.request.user.username
        initial['ip_data_hora_manual'] = get_client_ip(self.request)
        initial['data'] = timezone.localdate(timezone.now())
        initial['hora'] = timezone.localtime(timezone.now())
        return initial

    @transaction.atomic
    def form_valid(self, form):
        protocolo = form.save(commit=False)
        username = self.request.user.username
        self.logger.debug("user=" + username +
                          ". Tentando obter sequência de numeração.")
        numeracao = AppConfig.objects.last(
        ).sequencia_numeracao_protocolo
        if not numeracao:
            self.logger.error("user=" + username + ". É preciso definir a sequencia de "
                              "numeração na tabelas auxiliares!")
            msg = _('É preciso definir a sequencia de ' +
                    'numeração na tabelas auxiliares!')
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())

        if numeracao == 'A':
            numero_max = Protocolo.objects.filter(ano=timezone.now().year).aggregate(
                Max('numero')
            )['numero__max']
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year
            ).first()

            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim

            data_inicio_utc = from_date_to_datetime_utc(data_inicio)
            data_fim_utc = from_date_to_datetime_utc(data_fim)

            numero_max = Protocolo.objects.filter(
                Q(data__isnull=False, data__gte=data_inicio, data__lte=data_fim) | Q(
                    timestamp__isnull=False, timestamp__gte=data_inicio_utc,
                    timestamp__lte=data_fim_utc
                ) | Q(
                    timestamp_data_hora_manual__isnull=False,
                    timestamp_data_hora_manual__gte=data_inicio_utc,
                    timestamp_data_hora_manual__lte=data_fim_utc,
                )
            ).aggregate(Max('numero'))['numero__max']
        elif numeracao == 'U':
            numero_max = Protocolo.objects.all().aggregate(Max('numero'))[
                'numero__max']

        inicio_numeracao = AppConfig.objects.first().inicio_numeracao_protocolo
        numero = int(numero_max) if numero_max else 0
        protocolo.numero = (
            (numero + 1) if numero and numero >= inicio_numeracao else inicio_numeracao
        )

        protocolo.ano = timezone.now().year

        protocolo.tipo_protocolo = 0
        protocolo.tipo_processo = '1'  # TODO validar o significado
        protocolo.anulado = False

        if form.cleaned_data['autor']:
            protocolo.autor = form.cleaned_data['autor']
        protocolo.tipo_materia = TipoMateriaLegislativa.objects.get(
            id=self.request.POST['tipo_materia'])
        protocolo.numero_paginas = self.request.POST['numero_paginas']
        protocolo.observacao = self.request.POST['observacao']
        protocolo.assunto_ementa = self.request.POST['assunto_ementa']
        protocolo.user = self.request.user

        if form.cleaned_data['data_hora_manual'] == 'True':
            protocolo.timestamp = None
            protocolo.user_data_hora_manual = username
            protocolo.ip_data_hora_manual = get_client_ip(self.request)
        else:
            protocolo.data = None
            protocolo.hora = None
            protocolo.user_data_hora_manual = ''
            protocolo.ip_data_hora_manual = ''
        protocolo.save()

        data = form.cleaned_data
        if data['vincular_materia'] == 'True':
            materia = MateriaLegislativa.objects.get(
                ano=data['ano_materia'],
                numero=data['numero_materia'],
                tipo=data['tipo_materia']
            )

            materia.numero_protocolo = protocolo.numero
            materia.user = self.request.user
            materia.ip = get_client_ip(self.request)

            tz = timezone.get_current_timezone()
            materia.ultima_edicao = tz.localize(datetime.now())

            materia.save()

        return redirect(self.get_success_url(protocolo))

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        autores_ativos = self.autores_ativos()

        autores = []
        autores.append(['0', '------'])
        for a in autores_ativos:
            autores.append([a.id, a.__str__()])

        context['form'].fields['autor'].choices = autores
        return context

    def autores_ativos(self):
        lista_parlamentares = Parlamentar.objects.filter(
            ativo=True).values_list('id', flat=True)
        model_parlamentar = ContentType.objects.get_for_model(Parlamentar)
        autor_parlamentar = Autor.objects.filter(
            content_type=model_parlamentar, object_id__in=lista_parlamentares)

        lista_comissoes = Comissao.objects.filter(Q(
            data_extincao__isnull=True) | Q(
            data_extincao__gt=timezone.now())).values_list('id', flat=True)
        model_comissao = ContentType.objects.get_for_model(Comissao)
        autor_comissoes = Autor.objects.filter(
            content_type=model_comissao, object_id__in=lista_comissoes)
        autores_outros = Autor.objects.exclude(
            content_type__in=[model_parlamentar, model_comissao])
        q = autor_parlamentar | autor_comissoes | autores_outros
        return q


class ProtocoloMateriaTemplateView(PermissionRequiredMixin, TemplateView):

    template_name = "protocoloadm/MateriaTemplate.html"
    permission_required = ('protocoloadm.detail_protocolo', )

    def get_context_data(self, **kwargs):
        context = super(ProtocoloMateriaTemplateView, self).get_context_data(
            **kwargs)
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        context.update({'protocolo': protocolo})
        return context


class PesquisarDocumentoAdministrativoView(DocumentoAdministrativoMixin,
                                           PermissionRequiredMixin,
                                           FilterView):
    model = DocumentoAdministrativo
    filterset_class = DocumentoAdministrativoFilterSet
    paginate_by = 10
    permission_required = ('protocoloadm.list_documentoadministrativo', )

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarDocumentoAdministrativoView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        status_tramitacao = self.request.GET.get(
            'tramitacaoadministrativo__status')
        unidade_destino = self.request.GET.get(
            'tramitacaoadministrativo__unidade_tramitacao_destino')

        qs = self.get_queryset()

        qs = qs.prefetch_related("documentoacessorioadministrativo_set",
                                 "tramitacaoadministrativo_set",
                                 "tipo",
                                 "tramitacaoadministrativo_set__status",
                                 "tramitacaoadministrativo_set__unidade_tramitacao_local",
                                 "tramitacaoadministrativo_set__unidade_tramitacao_destino")

        if status_tramitacao and unidade_destino:
            lista = filtra_tramitacao_adm_destino_and_status(status_tramitacao,
                                                             unidade_destino)
            qs = qs.filter(id__in=lista).distinct()

        elif status_tramitacao:
            lista = filtra_tramitacao_adm_status(status_tramitacao)
            qs = qs.filter(id__in=lista).distinct()

        elif unidade_destino:
            lista = filtra_tramitacao_adm_destino(unidade_destino)
            qs = qs.filter(id__in=lista).distinct()

        if 'o' in self.request.GET and not self.request.GET['o']:
            qs = qs.order_by('-ano', '-numero')

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(PesquisarDocumentoAdministrativoView,
                        self).get_context_data(**kwargs)

        if self.paginate_by:
            paginator = context['paginator']
            page_obj = context['page_obj']
            context['page_range'] = make_pagination(
                page_obj.number, paginator.num_pages)

        return context

    def get(self, request, *args, **kwargs):
        super(PesquisarDocumentoAdministrativoView, self).get(request)
        # Se a pesquisa estiver quebrando com a paginação
        # Olhe esta função abaixo
        # Provavelmente você criou um novo campo no Form/FilterSet
        # Então a ordem da URL está diferente
        data = self.filterset.data
        if data and data.get('tipo') is not None:
            url = "&" + str(self.request.environ['QUERY_STRING'])
            if url.startswith("&page"):
                ponto_comeco = url.find('tipo=') - 1
                url = url[ponto_comeco:]
        else:
            url = ''
        self.filterset.form.fields['o'].label = _('Ordenação')
        # é usada essa verificação anônima para quando os documentos administrativos
        # estão no modo ostensivo, mas podem existir documentos administrativos
        # restritos
        if request.user.is_anonymous:
            length = self.object_list.filter(restrito=False).count()
        else:
            length = self.object_list.count()

        is_relatorio = url != '' and request.GET.get('relatorio', None)
        self.paginate_by = None if is_relatorio else self.paginate_by
        context = self.get_context_data(filter=self.filterset,
                                        filter_url=url,
                                        numero_res=length
                                        )
        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        if is_relatorio:
            return relatorio_doc_administrativos(request, context)
        else:
            return self.render_to_response(context)


class AnexadoCrud(MasterDetailCrud):
    model = Anexado
    parent_field = 'documento_principal'
    help_topic = 'documento_anexado'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['documento_anexado', 'data_anexacao']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = AnexadoForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = AnexadoForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['tipo'] = self.object.documento_anexado.tipo.id
            initial['numero'] = self.object.documento_anexado.numero
            initial['ano'] = self.object.documento_anexado.ano
            return initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'AnexadoDetail'


class DocumentoAnexadoEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = AnexadoEmLoteFilterSet
    template_name = 'protocoloadm/em_lote/anexado.html'
    permission_required = ('protocoloadm.add_anexado', )

    def get_context_data(self, **kwargs):
        context = super(
            DocumentoAnexadoEmLoteView, self
        ).get_context_data(**kwargs)

        context['root_pk'] = self.kwargs['pk']

        context['subnav_template_name'] = 'protocoloadm/subnav.yaml'

        context['title'] = _('Documentos Anexados em Lote')

        # Verifica se os campos foram preenchidos
        if not self.request.GET.get('tipo', " "):
            msg = _('Por favor, selecione um tipo de documento.')
            messages.add_message(self.request, messages.ERROR, msg)

            if not self.request.GET.get('data_0', " ") or not self.request.GET.get('data_1', " "):
                msg = _('Por favor, preencha as datas.')
                messages.add_message(self.request, messages.ERROR, msg)

            return context

        if not self.request.GET.get('data_0', " ") or not self.request.GET.get('data_1', " "):
            msg = _('Por favor, preencha as datas.')
            messages.add_message(self.request, messages.ERROR, msg)
            return context

        qr = self.request.GET.copy()
        if not len(qr):
            context['object_list'] = []
        else:
            context['temp_object_list'] = context['object_list'].order_by(
                'numero', '-ano')
            context['object_list'] = []
            for obj in context['temp_object_list']:
                if not obj.pk == int(context['root_pk']):
                    documento_principal = DocumentoAdministrativo.objects.get(
                        id=context['root_pk'])
                    documento_anexado = obj
                    is_anexado = Anexado.objects.filter(documento_principal=documento_principal,
                                                        documento_anexado=documento_anexado).exists()
                    if not is_anexado:
                        ciclico = False
                        anexados_anexado = Anexado.objects.filter(
                            documento_principal=documento_anexado)

                        while anexados_anexado and not ciclico:
                            anexados = []

                            for anexo in anexados_anexado:

                                if documento_principal == anexo.documento_anexado:
                                    ciclico = True
                                else:
                                    for a in Anexado.objects.filter(documento_principal=anexo.documento_anexado):
                                        anexados.append(a)

                            anexados_anexado = anexados

                        if not ciclico:
                            context['object_list'].append(obj)

        context['numero_res'] = len(context['object_list'])

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        marcados = request.POST.getlist('documento_id')

        data_anexacao = datetime.strptime(
            request.POST['data_anexacao'], "%d/%m/%Y"
        ).date()

        if request.POST['data_desanexacao'] == '':
            data_desanexacao = None
            v_data_desanexacao = data_anexacao
        else:
            data_desanexacao = datetime.strptime(
                request.POST['data_desanexacao'], "%d/%m/%Y"
            ).date()
            v_data_desanexacao = data_desanexacao

        if len(marcados) == 0:
            msg = _('Nenhum documento foi selecionado')
            messages.add_message(request, messages.ERROR, msg)

            if data_anexacao > v_data_desanexacao:
                msg = _('Data de anexação posterior à data de desanexação.')
                messages.add_message(request, messages.ERROR, msg)

            return self.get(request, self.kwargs)

        if data_anexacao > v_data_desanexacao:
            msg = _('Data de anexação posterior à data de desanexação.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, messages.ERROR, msg)

        principal = DocumentoAdministrativo.objects.get(pk=kwargs['pk'])
        for documento in DocumentoAdministrativo.objects.filter(id__in=marcados):
            anexado = Anexado()
            anexado.documento_principal = principal
            anexado.documento_anexado = documento
            anexado.data_anexacao = data_anexacao
            anexado.data_desanexacao = data_desanexacao
            anexado.save()

        msg = _('Documento(s) anexado(s).')
        messages.add_message(request, messages.SUCCESS, msg)

        success_url = reverse('sapl.protocoloadm:anexado_list', kwargs={
                              'pk': kwargs['pk']})
        return HttpResponseRedirect(success_url)


class TramitacaoAdmCrud(MasterDetailCrud):
    model = TramitacaoAdministrativo
    parent_field = 'documento'
    help_topic = 'unidade_tramitacao'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoAdmForm
        logger = logging.getLogger(__name__)

        def get_success_url(self):
            return reverse('sapl.protocoloadm:tramitacaoadministrativo_list', kwargs={
                'pk': self.kwargs['pk']})

        def get_initial(self):
            initial = super(CreateView, self).get_initial()
            local = DocumentoAdministrativo.objects.get(
                pk=self.kwargs['pk']).tramitacaoadministrativo_set.order_by(
                '-data_tramitacao',
                '-id').first()

            if local:
                initial['unidade_tramitacao_local'
                        ] = local.unidade_tramitacao_destino.pk
            else:
                initial['unidade_tramitacao_local'] = ''
            initial['data_tramitacao'] = timezone.now().date()
            initial['ip'] = get_client_ip(self.request)
            initial['user'] = self.request.user

            tz = timezone.get_current_timezone()
            initial['ultima_edicao'] = tz.localize(datetime.now())

            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            username = self.request.user.username

            ultima_tramitacao = TramitacaoAdministrativo.objects.filter(
                documento_id=self.kwargs['pk']).order_by(
                '-data_tramitacao',
                '-timestamp',
                '-id').first()

            # TODO: Esta checagem foi inserida na issue #2027, mas é mesmo
            # necessária?
            if ultima_tramitacao:
                if ultima_tramitacao.unidade_tramitacao_destino:
                    context['form'].fields[
                        'unidade_tramitacao_local'].choices = [
                        (ultima_tramitacao.unidade_tramitacao_destino.pk,
                         ultima_tramitacao.unidade_tramitacao_destino)]
                else:
                    self.logger.error('user=' + username + '. Unidade de tramitação destino '
                                      'da última tramitação não pode ser vazia!')
                    msg = _('Unidade de tramitação destino '
                            ' da última tramitação não pode ser vazia!')
                    messages.add_message(self.request, messages.ERROR, msg)

            primeira_tramitacao = not(TramitacaoAdministrativo.objects.filter(
                documento_id=int(kwargs['root_pk'])).exists())

            # Se não for a primeira tramitação daquela matéria, o campo
            # não pode ser modificado
            if not primeira_tramitacao:
                context['form'].fields[
                    'unidade_tramitacao_local'].widget.attrs['readonly'] = True
            return context

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = TramitacaoAdmEditForm
        logger = logging.getLogger(__name__)

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['ip'] = get_client_ip(self.request)
            initial['user'] = self.request.user

            tz = timezone.get_current_timezone()
            initial['ultima_edicao'] = tz.localize(datetime.now())

            return initial

    class ListView(DocumentoAdministrativoMixin, MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao',
                                                '-id')

    class DetailView(DocumentoAdministrativoMixin,
                     MasterDetailCrud.DetailView):

        template_name = 'protocoloadm/tramitacaoadministrativo_detail.html'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['user'] = self.request.user
            return context

    class DeleteView(MasterDetailCrud.DeleteView):

        logger = logging.getLogger(__name__)

        def delete(self, request, *args, **kwargs):
            tramitacao = TramitacaoAdministrativo.objects.get(
                id=self.kwargs['pk'])
            documento = tramitacao.documento
            url = reverse(
                'sapl.protocoloadm:tramitacaoadministrativo_list',
                kwargs={'pk': documento.id})

            ultima_tramitacao = \
                documento.tramitacaoadministrativo_set.order_by(
                    '-data_tramitacao',
                    '-id').first()

            if tramitacao.pk != ultima_tramitacao.pk:
                username = request.user.username
                self.logger.warning("User={}. Não é possível deletar a tramitação de pk={}. "
                                    "Somente a última tramitação (pk={}) pode ser deletada!."
                                    .format(username, tramitacao.pk, ultima_tramitacao.pk))
                msg = _('Somente a última tramitação pode ser deletada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(url)
            else:
                tramitacoes_deletar = [tramitacao]
                if documento.tramitacaoadministrativo_set.count() == 0:
                    documento.tramitacao = False
                    documento.save()
                tramitar_anexados = AppConfig.attr('tramitacao_documento')
                if tramitar_anexados:
                    docs_anexados = lista_anexados(documento)
                    for da in docs_anexados:
                        tram_anexada = da.tramitacaoadministrativo_set.last()
                        if compara_tramitacoes_doc(tram_anexada, tramitacao):
                            tramitacoes_deletar.append(tram_anexada)
                            if da.tramitacaoadministrativo_set.count() == 0:
                                da.tramitacao = False
                                da.save()
                TramitacaoAdministrativo.objects.filter(
                    id__in=[t.id for t in tramitacoes_deletar]).delete()

                # TODO: otimizar para passar a lista de matérias
                # for tramitacao in tramitacoes_deletar:
                #    post_delete_signal.send(sender=None,
                # instance=tramitacao,
                #                            operation='C',
                #                            request=self.request)

                return HttpResponseRedirect(url)


class DocumentoAcessorioAdministrativoCrud(MasterDetailCrud):
    model = DocumentoAcessorioAdministrativo
    parent_field = 'documento'
    help_topic = 'numeracao_docsacess'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'tipo',
                            'data', 'autor',
                            'assunto']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DocumentoAcessorioAdministrativoForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = DocumentoAcessorioAdministrativoForm

    class ListView(DocumentoAdministrativoMixin, MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data', '-id')

    class DetailView(DocumentoAdministrativoMixin,
                     MasterDetailCrud.DetailView):
        pass


def atualizar_numero_documento(request):
    tipo = TipoDocumentoAdministrativo.objects.get(pk=request.GET['tipo'])
    ano = request.GET['ano']

    param = {'tipo': tipo}
    param['ano'] = ano if ano else timezone.now().year

    doc = DocumentoAdministrativo.objects.filter(**param).order_by(
        'tipo', 'ano', 'numero').values_list('numero', 'ano').last()

    if doc:
        response = JsonResponse({'numero': int(doc[0]) + 1,
                                 'ano': doc[1]})
    else:
        response = JsonResponse(
            {'numero': 1, 'ano': ano})

    return response


class DesvincularDocumentoView(PermissionRequiredMixin, CreateView):
    template_name = 'protocoloadm/anular_protocoloadm.html'
    form_class = DesvincularDocumentoForm
    form_valid_message = _('Documento desvinculado com sucesso!')
    permission_required = ('protocoloadm.action_anular_protocolo', )

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def form_valid(self, form):
        documento = DocumentoAdministrativo.objects.get(numero=form.cleaned_data['numero'],
                                                        ano=form.cleaned_data['ano'],
                                                        tipo=form.cleaned_data['tipo'])
        documento.protocolo = None

        documento.user = self.request.user
        documento.ip = get_client_ip(self.request)

        tz = timezone.get_current_timezone()
        documento.ultima_edicao = tz.localize(datetime.now())

        documento.save()
        return redirect(self.get_success_url())


class DesvincularMateriaView(PermissionRequiredMixin, FormView):
    template_name = 'protocoloadm/anular_protocoloadm.html'
    form_class = DesvincularMateriaForm
    form_valid_message = _('Matéria desvinculado com sucesso!')
    permission_required = ('protocoloadm.action_anular_protocolo', )

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def form_valid(self, form):
        materia = MateriaLegislativa.objects.get(
            numero=form.cleaned_data['numero'],
            ano=form.cleaned_data['ano'],
            tipo=form.cleaned_data['tipo']
        )

        materia.numero_protocolo = None

        materia.user = self.request.user
        materia.ip = get_client_ip(self.request)

        tz = timezone.get_current_timezone()
        materia.ultima_edicao = tz.localize(datetime.now())

        materia.save()
        return redirect(self.get_success_url())


class ImpressosView(PermissionRequiredMixin, TemplateView):
    template_name = 'materia/impressos/impressos.html'
    permission_required = ('materia.can_access_impressos', )


class FichaPesquisaAdmView(PermissionRequiredMixin, FormView):
    form_class = FichaPesquisaAdmForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos', )

    def form_valid(self, form):
        tipo_documento = form.data['tipo_documento']
        data_inicial = form.data['data_inicial']
        data_final = form.data['data_final']

        url = reverse('sapl.materia:impressos_ficha_seleciona_adm')
        url = url + '?tipo=%s&data_inicial=%s&data_final=%s' % (
            tipo_documento, data_inicial, data_final)

        return HttpResponseRedirect(url)


class FichaSelecionaAdmView(PermissionRequiredMixin, FormView):
    logger = logging.getLogger(__name__)
    form_class = FichaSelecionaAdmForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos', )

    def get_context_data(self, **kwargs):
        if ('tipo' not in self.request.GET or
            'data_inicial' not in self.request.GET or
                'data_final' not in self.request.GET):
            return HttpResponseRedirect(reverse(
                'sapl.materia:impressos_ficha_pesquisa_adm'))

        context = super(FichaSelecionaAdmView, self).get_context_data(
            **kwargs)

        tipo = self.request.GET['tipo']
        data_inicial = datetime.strptime(
            self.request.GET['data_inicial'], "%d/%m/%Y").date()
        data_final = datetime.strptime(
            self.request.GET['data_final'], "%d/%m/%Y").date()

        documento_list = DocumentoAdministrativo.objects.filter(
            tipo=tipo,
            data__range=(data_inicial, data_final))
        context['quantidade'] = len(documento_list)
        documento_list = documento_list[:100]

        context['form'].fields['documento'].choices = [
            (d.id, str(d)) for d in documento_list]

        username = self.request.user.username

        if context['quantidade'] > 100:
            self.logger.info('user=' + username + '. Sua pesquisa (tipo={}, data_inicial={}, data_final={}) retornou mais do que '
                             '100 impressos. Por questões de '
                             'performance, foram retornados '
                             'apenas os 100 primeiros. Caso '
                             'queira outros, tente fazer uma '
                             'pesquisa mais específica'.format(tipo, data_inicial, data_final))
            messages.info(self.request, _('Sua pesquisa retornou mais do que '
                                          '100 impressos. Por questões de '
                                          'performance, foram retornados '
                                          'apenas os 100 primeiros. Caso '
                                          'queira outros, tente fazer uma '
                                          'pesquisa mais específica'))

        return context

    def form_valid(self, form):
        context = {}
        username = self.request.user.username

        try:
            self.logger.debug(
                "user=" + username + ". Tentando obter objeto DocumentoAdministrativo com id={}".format(form.data['documento']))
            documento = DocumentoAdministrativo.objects.get(
                id=form.data['documento'])
        except ObjectDoesNotExist:
            self.logger.error(
                "user=" + username + ". Este DocumentoAdministrativo não existe (id={}).".format(form.data['documento']))
            mensagem = _('Este Documento Administrativo não existe.')
            self.messages.add_message(self.request, messages.INFO, mensagem)

            return self.render_to_response(context)
        if len(documento.assunto) > 201:
            documento.assunto = documento.assunto[0:200] + '[...]'
        context['documento'] = documento

        return gerar_pdf_impressos(self.request, context,
                                   'materia/impressos/ficha_adm_pdf.html')


class PrimeiraTramitacaoEmLoteAdmView(PermissionRequiredMixin, FilterView):
    filterset_class = PrimeiraTramitacaoEmLoteAdmFilterSet
    template_name = 'protocoloadm/em_lote/tramitacaoadm.html'
    permission_required = ('protocoloadm.add_tramitacaoadministrativo', )

    primeira_tramitacao = True

    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(PrimeiraTramitacaoEmLoteAdmView,
                        self).get_context_data(**kwargs)

        context['subnav_template_name'] = 'protocoloadm/em_lote/subnav_em_lote.yaml'
        context['primeira_tramitacao'] = self.primeira_tramitacao

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        context['object_list'] = context['object_list'].order_by(
            'ano', 'numero')
        qr = self.request.GET.copy()

        form = TramitacaoEmLoteAdmForm()
        context['form'] = form

        if self.primeira_tramitacao:
            context['title'] = _('Primeira Tramitação em Lote')
            # Pega somente documentos que não possuem tramitação
            context['object_list'] = [obj for obj in context['object_list']
                                      if obj.tramitacaoadministrativo_set.all().count() == 0]
        else:
            context['title'] = _('Tramitação em Lote')
            context['form'].fields['unidade_tramitacao_local'].initial = UnidadeTramitacao.objects.get(
                id=qr['tramitacaoadministrativo__unidade_tramitacao_destino'])

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        ip = get_client_ip(request)

        tz = timezone.get_current_timezone()
        ultima_edicao = tz.localize(datetime.now())

        documentos_ids = request.POST.getlist('documentos')
        if not documentos_ids:
            msg = _("Escolha algum Documento para ser tramitado.")
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        form = TramitacaoEmLoteAdmForm(request.POST,
                                       initial={'documentos': documentos_ids,
                                                'user': user, 'ip': ip,
                                                'ultima_edicao': ultima_edicao})

        if form.is_valid():
            form.save()

            msg = _('Tramitação completa.')
            self.logger.info('user=' + user.username +
                             '. Tramitação completa.')
            messages.add_message(request, messages.SUCCESS, msg)
            return self.get_success_url()

        return self.form_invalid(form)

    def get_success_url(self):
        return HttpResponseRedirect(reverse('sapl.protocoloadm:primeira_tramitacao_em_lote_docadm'))

    def form_invalid(self, form, *args, **kwargs):
        for key, erros in form.errors.items():
            if not key == '__all__':
                [messages.add_message(
                    self.request, messages.ERROR, form.fields[key].label + ": " + e) for e in erros]
            else:
                [messages.add_message(self.request, messages.ERROR, e)
                 for e in erros]
        return self.get(self.request, kwargs, {'form': form})


class TramitacaoEmLoteAdmView(PrimeiraTramitacaoEmLoteAdmView):
    filterset_class = TramitacaoEmLoteAdmFilterSet

    primeira_tramitacao = False

    def get_context_data(self, **kwargs):
        context = super(TramitacaoEmLoteAdmView,
                        self).get_context_data(**kwargs)

        qr = self.request.GET.copy()

        context['primeira_tramitacao'] = self.primeira_tramitacao

        if ('tramitacao__status' in qr and
                'tramitacao__unidade_tramitacao_destino' in qr and
                qr['tramitacao__status'] and
                qr['tramitacao__unidade_tramitacao_destino']):
            lista = self.filtra_tramitacao_destino_and_status(
                qr['tramitacao__status'],
                qr['tramitacao__unidade_tramitacao_destino'])
            context['object_list'] = context['object_list'].filter(
                id__in=lista).distinct()

        return context

    def pega_ultima_tramitacao(self):
        return TramitacaoAdministrativo.objects.values(
            'documento_id').annotate(data_encaminhamento=Max(
                'data_encaminhamento'),
            id=Max('id')).values_list('id', flat=True)

    def filtra_tramitacao_status(self, status):
        lista = self.pega_ultima_tramitacao()
        return TramitacaoAdministrativo.objects.filter(
            id__in=lista,
            status=status).distinct().values_list('documento_id', flat=True)

    def filtra_tramitacao_destino(self, destino):
        lista = self.pega_ultima_tramitacao()
        return TramitacaoAdministrativo.objects.filter(
            id__in=lista,
            unidade_tramitacao_destino=destino).distinct().values_list(
                'documento_id', flat=True)

    def filtra_tramitacao_destino_and_status(self, status, destino):
        lista = self.pega_ultima_tramitacao()
        return TramitacaoAdministrativo.objects.filter(
            id__in=lista,
            status=status,
            unidade_tramitacao_destino=destino).distinct().values_list(
                'documento_id', flat=True)


def apaga_protocolos(request, ano, numero_protocolo=None):
    kwargs = {'ano__in': ano}
    if numero_protocolo:
        kwargs.update({'numero__gte': numero_protocolo})

    all_protocolos = Protocolo.objects.filter(**kwargs)

    for doc in DocumentoAdministrativo.objects.filter(protocolo__in=all_protocolos):
        doc.protocolo = None
        doc.save()

    for ml in MateriaLegislativa.objects.filter(ano__in=ano, numero_protocolo__in=all_protocolos.values_list('numero')):
        ml.numero_protocolo = None
        ml.save()

    # for deleted_object in all_protocolos:
    # post_delete_signal.send(sender=None,
    #                            instance=deleted_object,
    #                            operation='D',
    #                            request=request
    #                            )
    all_protocolos.delete()


@staff_member_required
def apaga_protocolos_view(request):
    if request.method == "GET":
        if Protocolo.objects.exists():
            intervalo_data = Protocolo.objects.all().distinct(
                'ano').values_list('ano', flat=True).order_by('-ano')
        else:
            intervalo_data = None
        return render(request, "protocoloadm/deleta_todos_protocolos.html", {'intervalo_data': intervalo_data})

    elif request.method == "POST":
        password = request.POST.get('senha')
        valid = request.user.check_password(password)
        if valid:
            anos = request.POST.getlist('ano')
            numero_protocolo = request.POST.get('numero_protocolo')
            apaga_protocolos(request, anos, numero_protocolo)
            return JsonResponse({'type': 'success', 'msg': ''})
        else:
            return JsonResponse({'type': 'error', 'msg': 'Senha Incorreta'})


class VinculoDocAdminMateriaCrud(MasterDetailCrud):
    model = VinculoDocAdminMateria
    parent_field = 'documento'
    help_topic = 'vinculodocadminmateria'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_anexacao', ('materia', 'materia__ementa')]

        @property
        def verbose_name(self):
            return _('Vinculo')

        @property
        def verbose_name_plural(self):
            return _('Vinculos')

        @property
        def title(self):
            return self.object.documento.epigrafe

    class CreateView(MasterDetailCrud.CreateView):
        form_class = VinculoDocAdminMateriaForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = VinculoDocAdminMateriaForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title'] = self.object.documento.epigrafe
            return context

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['tipo'] = self.object.materia.tipo.id
            initial['numero'] = self.object.materia.numero
            initial['ano'] = self.object.materia.ano
            return initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'VinculoDocAdminMateriaDetail'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title'] = self.object.documento.epigrafe
            return context


"""

class VinculoDocAdminMateriaEmLoteView(PermissionRequiredMixin, FilterView):
    filterset_class = AnexadaEmLoteFilterSet
    template_name = 'materia/em_lote/anexada.html'
    permission_required = ('materia.add_documentoacessorio',)

    def get_context_data(self, **kwargs):
        context = super(MateriaAnexadaEmLoteView,
                        self).get_context_data(**kwargs)

        context['root_pk'] = self.kwargs['pk']

        context['subnav_template_name'] = 'materia/subnav.yaml'

        context['title'] = _('Matérias Anexadas em Lote')

        # Verifica se os campos foram preenchidos
        if not self.request.GET.get('tipo', " "):
            msg = _('Por favor, selecione um tipo de matéria.')
            messages.add_message(self.request, messages.ERROR, msg)

            if not self.request.GET.get('data_apresentacao_0', " ") or not self.request.GET.get('data_apresentacao_1', " "):
                msg = _('Por favor, preencha as datas.')
                messages.add_message(self.request, messages.ERROR, msg)

            return context

        if not self.request.GET.get('data_apresentacao_0', " ") or not self.request.GET.get('data_apresentacao_1', " "):
            msg = _('Por favor, preencha as datas.')
            messages.add_message(self.request, messages.ERROR, msg)
            return context

        qr = self.request.GET.copy()
        if not len(qr):
            context['object_list'] = []
        else:
            context['object_list'] = context['object_list'].order_by(
                'numero', '-ano')
            principal = MateriaLegislativa.objects.get(pk=self.kwargs['pk'])
            not_list = [self.kwargs['pk']] + \
                [m for m in principal.materia_principal_set.all(
                ).values_list('materia_anexada_id', flat=True)]
            context['object_list'] = context['object_list'].exclude(
                pk__in=not_list)

            context['temp_object_list'] = context['object_list']
            context['object_list'] = []
            for obj in context['temp_object_list']:
                materia_anexada = obj
                ciclico = False
                anexadas_anexada = Anexada.objects.filter(
                    materia_principal=materia_anexada
                )

                while anexadas_anexada and not ciclico:
                    anexadas = []

                    for anexa in anexadas_anexada:

                        if principal == anexa.materia_anexada:
                            ciclico = True
                        else:
                            for a in Anexada.objects.filter(materia_principal=anexa.materia_anexada):
                                anexadas.append(a)

                    anexadas_anexada = anexadas

                if not ciclico:
                    context['object_list'].append(obj)

        context['numero_res'] = len(context['object_list'])

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')

        data_anexacao = datetime.strptime(
            request.POST['data_anexacao'], "%d/%m/%Y").date()

        if request.POST['data_desanexacao'] == '':
            data_desanexacao = None
            v_data_desanexacao = data_anexacao
        else:
            data_desanexacao = datetime.strptime(
                request.POST['data_desanexacao'], "%d/%m/%Y").date()
            v_data_desanexacao = data_desanexacao

        if len(marcadas) == 0:
            msg = _('Nenhuma máteria foi selecionada.')
            messages.add_message(request, messages.ERROR, msg)

            if data_anexacao > v_data_desanexacao:
                msg = _('Data de anexação posterior à data de desanexação.')
                messages.add_message(request, messages.ERROR, msg)

            return self.get(request, self.kwargs)

        if data_anexacao > v_data_desanexacao:
            msg = _('Data de anexação posterior à data de desanexação.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        principal = MateriaLegislativa.objects.get(pk=kwargs['pk'])
        for materia in MateriaLegislativa.objects.filter(id__in=marcadas):

            anexada = Anexada()
            anexada.materia_principal = principal
            anexada.materia_anexada = materia
            anexada.data_anexacao = data_anexacao
            anexada.data_desanexacao = data_desanexacao
            anexada.save()

        msg = _('Matéria(s) anexada(s).')
        messages.add_message(request, messages.SUCCESS, msg)

        success_url = reverse('sapl.materia:anexada_list',
                              kwargs={'pk': kwargs['pk']})
        return HttpResponseRedirect(success_url)
"""
