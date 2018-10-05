from datetime import datetime
from random import choice
from string import ascii_letters, digits

from braces.views import FormValidMessageMixin
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Max, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, CreateView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.edit import FormView
from django_filters.views import FilterView

import sapl
from sapl.base.models import Autor, CasaLegislativa
from sapl.comissoes.models import Comissao
from sapl.crud.base import Crud, CrudAux, MasterDetailCrud, make_pagination
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Legislatura, Parlamentar
from sapl.protocoloadm.models import Protocolo
from sapl.utils import (create_barcode, get_base_url, get_client_ip,
                        get_mime_type_from_file_extension,
                        show_results_filter_set)
from sapl.base.email_utils import do_envia_email_confirmacao
from .forms import (AcompanhamentoDocumentoForm, AnularProcoloAdmForm,
                    DocumentoAcessorioAdministrativoForm,
                    DocumentoAdministrativoFilterSet,
                    DocumentoAdministrativoForm, ProtocoloDocumentForm,
                    ProtocoloFilterSet, ProtocoloMateriaForm,
                    TramitacaoAdmEditForm, TramitacaoAdmForm,
                    DesvincularDocumentoForm, DesvincularMateriaForm,
                    filtra_tramitacao_adm_destino_and_status,
                    filtra_tramitacao_adm_destino, filtra_tramitacao_adm_status)
from .models import (AcompanhamentoDocumento, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)
from sapl.base.signals import tramitacao_signal


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
    try:
        materia = MateriaLegislativa.objects.get(
            tipo=tipo, ano=ano,numero=numero)
        autoria = materia.autoria_set.first()
        content = {'ementa': materia.ementa.strip(),
                    'ano':materia.ano, 'numero':materia.numero}
        if autoria:
            content.update({'autor': autoria.autor.pk,
                            'tipo_autor':autoria.autor.tipo.pk})
        response = JsonResponse(content)
    except Exception as e:
        response = JsonResponse({'error':e})
    return response

def doc_texto_integral(request, pk):
    can_see = True

    if not request.user.is_authenticated():
        app_config = sapl.base.models.AppConfig.objects.last()
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

    def get_redirect_url(self, email):
        msg = _('Este documento está sendo acompanhado pelo e-mail: %s') % (
            email)
        messages.add_message(self.request, messages.SUCCESS, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        documento_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')

        try:
            acompanhar = AcompanhamentoDocumento.objects.get(
                documento_id=documento_id,
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
        msg = _('Você parou de acompanhar este Documento.')
        messages.add_message(self.request, messages.INFO, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        materia_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')

        try:
            AcompanhamentoDocumento.objects.get(documento_id=documento_id,
                                              hash=hash_txt).delete()
        except ObjectDoesNotExist:
            pass

        return HttpResponseRedirect(self.get_success_url())


class AcompanhamentoDocumentoView(CreateView):
    template_name = "protocoloadm/acompanhamento_documento.html"

    def get_random_chars(self):
        s = ascii_letters + digits
        return ''.join(choice(s) for i in range(choice([6, 7])))

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)

        return self.render_to_response(
            {'form': AcompanhamentoDocumentoForm(),
             'documento': documento})

    def post(self, request, *args, **kwargs):
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

                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                         de mensagens e clique no link que nós enviamos para \
                         confirmar o acompanhamento deste documento.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Caso esse Acompanhamento já exista
            # avisa ao usuário que esse documento já está sendo acompanhado
            else:
                msg = _('Este e-mail já está acompanhando esse documento.')
                messages.add_message(request, messages.INFO, msg)

                return self.render_to_response(
                    {'form': form,
                     'documento': documento,
                     'error': _('Esse documento já está\
                     sendo acompanhada por este e-mail.')})
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
        app_config = sapl.base.models.AppConfig.objects.last()
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

        @property
        def cancel_url(self):
            return self.search_url

    class UpdateView(Crud.UpdateView):
        form_class = DocumentoAdministrativoForm
        layout_key = None

        def get_initial(self):
            if self.object.protocolo:
                p = self.object.protocolo
                return {'ano_protocolo': p.ano,
                        'numero_protocolo': p.numero}

    class DetailView(DocumentoAdministrativoMixin, Crud.DetailView):

        def get(self, *args, **kwargs):
            pk = self.kwargs['pk']
            documento = DocumentoAdministrativo.objects.get(id=pk)
            if documento.restrito and self.request.user.is_anonymous():
                return redirect('/')
            return super(Crud.DetailView, self).get(args, kwargs)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            self.layout_display[0]['rows'][-1][0]['text'] = (
                '<a href="%s"></a>' % reverse(
                    'sapl.protocoloadm:doc_texto_integral',
                    kwargs={'pk': self.object.pk}))
            return context

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
    form_class = AnularProcoloAdmForm
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
    template_name = "protocoloadm/protocolar_documento.html"
    form_class = ProtocoloDocumentForm
    form_valid_message = _('Protocolo cadastrado com sucesso!')
    permission_required = ('protocoloadm.add_protocolo', )

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.object.id})

    def form_valid(self, form):
        protocolo = form.save(commit=False)
        try:
            numeracao = sapl.base.models.AppConfig.objects.last(
            ).sequencia_numeracao
        except AttributeError:
            msg = _('É preciso definir a sequencia de ' +
                    'numeração na tabelas auxiliares!')
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())

        if numeracao == 'A':
            numero = Protocolo.objects.filter(
                ano=timezone.now().year).aggregate(Max('numero'))
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year).first()
            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim
            numero = Protocolo.objects.filter(
                data__gte=data_inicio,
                data__lte=data_fim).aggregate(
                Max('numero'))
        elif numeracao == 'U':
            numero = Protocolo.objects.all().aggregate(Max('numero'))

        protocolo.tipo_processo = '0'  # TODO validar o significado
        protocolo.anulado = False
        if not protocolo.numero:
            protocolo.numero = (numero['numero__max'] + 1) if numero['numero__max'] else 1
        elif protocolo.numero < (numero['numero__max'] + 1) if numero['numero__max'] else 0:
            msg = _('Número de protocolo deve ser maior que {}').format(numero['numero__max'])
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())
        protocolo.ano = timezone.now().year
        protocolo.assunto_ementa = self.request.POST['assunto']
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
        return doc


class ProtocoloMostrarView(PermissionRequiredMixin, TemplateView):

    template_name = "protocoloadm/protocolo_mostrar.html"
    permission_required = ('protocoloadm.detail_protocolo', )

    def get_context_data(self, **kwargs):
        context = super(ProtocoloMostrarView, self).get_context_data(**kwargs)
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])

        if protocolo.tipo_materia:
            try:
                materia = MateriaLegislativa.objects.get(
                    numero_protocolo=protocolo.numero, ano=protocolo.ano)
            except ObjectDoesNotExist:
                context['materia'] = None
            else:
                context['materia'] = materia

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

        context.update({"protocolo": protocolo,
                        "barcode": barcode,
                        "autenticacao": autenticacao})
        return context


class ProtocoloMateriaView(PermissionRequiredMixin, CreateView):

    template_name = "protocoloadm/protocolar_materia.html"
    form_class = ProtocoloMateriaForm
    form_valid_message = _('Matéria cadastrada com sucesso!')
    permission_required = ('protocoloadm.add_protocolo',)

    def get_success_url(self, protocolo):
        return reverse('sapl.protocoloadm:materia_continuar', kwargs={
            'pk': protocolo.pk})

    def form_valid(self, form):
        protocolo = form.save(commit=False)
        try:
            numeracao = sapl.base.models.AppConfig.objects.last(
            ).sequencia_numeracao
        except AttributeError:
            msg = _('É preciso definir a sequencia de ' +
                    'numeração na tabelas auxiliares!')
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())

        if numeracao == 'A':
            numero = Protocolo.objects.filter(
                ano=timezone.now().year).aggregate(Max('numero'))
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year).first()
            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim
            numero = Protocolo.objects.filter(
                data__gte=data_inicio,
                data__lte=data_fim).aggregate(
                Max('numero'))
        elif numeracao == 'U':
            numero = Protocolo.objects.all().aggregate(Max('numero'))

        if numeracao is None:
            numero['numero__max'] = 0

        if not protocolo.numero:
            protocolo.numero = (numero['numero__max'] + 1) if numero['numero__max'] else 1
        if numero['numero__max']:
            if protocolo.numero < (numero['numero__max'] + 1):
                msg = _('Número de protocolo deve ser maior que {}').format(numero['numero__max'])
                messages.add_message(self.request, messages.ERROR, msg)
                return self.render_to_response(self.get_context_data())
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

        protocolo.save()
        data = form.cleaned_data
        if data['vincular_materia'] == 'True':
            materia = MateriaLegislativa.objects.get(ano=data['ano_materia'],
                                                     numero=data['numero_materia'],
                                                     tipo=data['tipo_materia'])
            materia.numero_protocolo = protocolo.numero
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

        length = self.object_list.count()
        context = self.get_context_data(filter=self.filterset,
                                        filter_url=url,
                                        numero_res=length
                                        )

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)


class TramitacaoAdmCrud(MasterDetailCrud):
    model = TramitacaoAdministrativo
    parent_field = 'documento'
    help_topic = 'unidade_tramitacao'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoAdmForm

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
            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            primeira_tramitacao = not(TramitacaoAdministrativo.objects.filter(
                documento_id=int(kwargs['root_pk'])).exists())

            # Se não for a primeira tramitação daquela matéria, o campo
            # não pode ser modificado
            if not primeira_tramitacao:
                context['form'].fields[
                    'unidade_tramitacao_local'].widget.attrs['disabled'] = True
            return context

        def form_valid(self, form):
            self.object = form.save()

            try:
                tramitacao_signal.send(sender=TramitacaoAdministrativo,
                                       post=self.object,
                                       request=self.request)
            except Exception as e:
                # TODO log error
                msg = _('Tramitação criada, mas e-mail de acompanhamento '
                    'de documento não enviado. A não configuração do'
                    ' servidor de e-mail impede o envio de aviso de tramitação')
                messages.add_message(self.request, messages.WARNING, msg)
                return HttpResponseRedirect(self.get_success_url())
            return super().form_valid(form)

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = TramitacaoAdmEditForm
        def form_valid(self, form):
            self.object = form.save()
            try:
                tramitacao_signal.send(sender=TramitacaoAdministrativo,
                                       post=self.object,
                                       request=self.request)
            except Exception as e:
                # TODO log error
                msg = _('Tramitação criada, mas e-mail de acompanhamento '
                    'de documento não enviado. A não configuração do'
                    ' servidor de e-mail impede o envio de aviso de tramitação')
                messages.add_message(self.request, messages.WARNING, msg)
                return HttpResponseRedirect(self.get_success_url())
            return super().form_valid(form)

    class ListView(DocumentoAdministrativoMixin, MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao',
                                                '-id')

    class DetailView(DocumentoAdministrativoMixin,
                     MasterDetailCrud.DetailView):
        pass

    class DeleteView(MasterDetailCrud.DeleteView):

        def delete(self, request, *args, **kwargs):
            tramitacao = TramitacaoAdministrativo.objects.get(
                id=self.kwargs['pk'])
            documento = DocumentoAdministrativo.objects.get(
                id=tramitacao.documento.id)
            url = reverse(
                'sapl.protocoloadm:tramitacaoadministrativo_list',
                kwargs={'pk': tramitacao.documento.id})

            ultima_tramitacao = \
                documento.tramitacaoadministrativo_set.order_by(
                    '-data_tramitacao',
                    '-id').first()

            if tramitacao.pk != ultima_tramitacao.pk:
                msg = _('Somente a última tramitação pode ser deletada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(url)
            else:
                tramitacao.delete()
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
        materia = MateriaLegislativa.objects.get(numero=form.cleaned_data['numero'],
                                                        ano=form.cleaned_data['ano'],
                                                        tipo=form.cleaned_data['tipo'])
        materia.numero_protocolo = None
        materia.save()
        return redirect(self.get_success_url())
