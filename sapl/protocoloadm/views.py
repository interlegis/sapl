from datetime import date, datetime


from braces.views import FormValidMessageMixin
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, ListView
from django.views.generic.base import TemplateView
from django_filters.views import FilterView

import sapl
from sapl.base.models import Autor
from sapl.crud.base import Crud, CrudAux, MasterDetailCrud, make_pagination
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.utils import create_barcode, get_client_ip

from .forms import (AnularProcoloAdmForm, DocumentoAcessorioAdministrativoForm,
                    DocumentoAdministrativoFilterSet,
                    DocumentoAdministrativoForm, ProtocoloDocumentForm,
                    ProtocoloFilterSet, ProtocoloMateriaForm,
                    TramitacaoAdmEditForm, TramitacaoAdmForm)
from .models import (DocumentoAcessorioAdministrativo, DocumentoAdministrativo,
                     Protocolo, StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import Protocolo
from sapl.comissoes.models import Comissao
from django.contrib.contenttypes.models import ContentType

TipoDocumentoAdministrativoCrud = CrudAux.build(
    TipoDocumentoAdministrativo, '')


# ProtocoloDocumentoCrud = Crud.build(Protocolo, '')
# FIXME precisa de uma chave diferente para o layout
# ProtocoloMateriaCrud = Crud.build(Protocolo, '')


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


class DocumentoAdministrativoMixin:

    def has_permission(self):
        app_config = sapl.base.models.AppConfig.objects.last()
        if app_config and app_config.documentos_administrativos == 'O':
            return True

        return super().has_permission()


class DocumentoAdministrativoCrud(Crud):
    model = DocumentoAdministrativo
    help_path = ''

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data',
                            'numero_protocolo', 'assunto',
                            'interessado', 'tramitacao', 'texto_integral']

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesq_doc_adm'))

        @property
        def list_url(self):
            return ''

    class ListView(DocumentoAdministrativoMixin, Crud.ListView):
        pass

    class CreateView(DocumentoAdministrativoMixin, Crud.CreateView):
        form_class = DocumentoAdministrativoForm
        layout_key = None

    class UpdateView(DocumentoAdministrativoMixin, Crud.UpdateView):
        form_class = DocumentoAdministrativoForm
        layout_key = None

        def get_initial(self):
            if self.object.protocolo:
                p = self.object.protocolo
                return {'ano_protocolo': p.ano,
                        'numero_protocolo': p.numero}

    class DetailView(DocumentoAdministrativoMixin, Crud.DetailView):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            self.layout_display[0]['rows'][-1][0]['text'] = (
                '<a href="%s"></a>' % reverse(
                    'sapl.protocoloadm:doc_texto_integral',
                    kwargs={'pk': self.object.pk}))
            return context

    class DeleteView(DocumentoAdministrativoMixin, Crud.DeleteView):
        def get_success_url(self):
            return reverse('sapl.protocoloadm:pesq_doc_adm', kwargs={})


class StatusTramitacaoAdministrativoCrud(CrudAux):
    model = StatusTramitacaoAdministrativo
    help_path = ''

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

        qs = self.get_queryset().order_by('ano', 'numero')

        qs = qs.distinct()

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

        context['title'] = _('Pesquisa de Protocolos')

        return context

    def get(self, request, *args, **kwargs):
        super(ProtocoloPesquisaView, self).get(request)

        # Se a pesquisa estiver quebrando com a paginação
        # Olhe esta função abaixo
        # Provavelmente você criou um novo campo no Form/FilterSet
        # Então a ordem da URL está diferente
        data = self.filterset.data
        if (data and data.get('numero') is not None):
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
        f = form.save(commit=False)

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
                ano=date.today().year).aggregate(Max('numero'))
        elif numeracao == 'L':
            legislatura = Legislatura.objects.last()
            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim
            numero = Protocolo.objects.filter(
                data__gte=data_inicio, data__lte=data_fim).aggregate(
                    Max('numero'))
        elif numeracao == 'U':
            numero = Protocolo.objects.all().aggregate(Max('numero'))

        f.tipo_processo = '0'  # TODO validar o significado
        f.anulado = False
        f.numero = (numero['numero__max'] + 1) if numero['numero__max'] else 1
        f.ano = datetime.now().year
        f.data = datetime.now().date()
        f.hora = datetime.now().time()
        f.timestamp = datetime.now()
        f.assunto_ementa = self.request.POST['assunto']

        f.save()
        self.object = f
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
        curr_year = datetime.now().date().year

        numero_max = DocumentoAdministrativo.objects.filter(
            tipo=protocolo.tipo_documento, ano=curr_year
        ).aggregate(Max('numero'))['numero__max']

        doc = {}
        doc['tipo'] = protocolo.tipo_documento
        doc['ano'] = curr_year
        doc['data'] = datetime.today()
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
            # data is not i18n sensitive 'Y-m-d' is the right format.
            autenticacao = str(protocolo.tipo_processo) + \
                protocolo.data.strftime("%Y/%m/%d") + \
                str(protocolo.numero).zfill(6)

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
                ano=date.today().year).aggregate(Max('numero'))
        elif numeracao == 'U':
            numero = Protocolo.objects.all().aggregate(Max('numero'))

        if numeracao is None:
            numero['numero__max'] = 0

        protocolo = Protocolo()

        protocolo.numero = (
            numero['numero__max'] + 1) if numero['numero__max'] else 1
        protocolo.ano = datetime.now().year
        protocolo.data = datetime.now().date()
        protocolo.hora = datetime.now().time()
        protocolo.timestamp = datetime.now()

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
            lista_parlamentares = Parlamentar.objects.filter(ativo=True).values_list('id', flat=True)
            model_parlamentar = ContentType.objects.get_for_model(Parlamentar)
            autor_parlamentar = Autor.objects.filter(content_type=model_parlamentar, object_id__in=lista_parlamentares)

            lista_comissoes = Comissao.objects.filter(Q(data_extincao__isnull=True)|Q(data_extincao__gt=date.today())).values_list('id', flat=True)
            model_comissao = ContentType.objects.get_for_model(Comissao)
            autor_comissoes = Autor.objects.filter(content_type=model_comissao, object_id__in=lista_comissoes)
            autores_outros = Autor.objects.exclude(content_type__in=[model_parlamentar, model_comissao])
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

        qs = self.get_queryset()

        qs = qs.distinct()

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
        if (data and data.get('tipo') is not None):
            url = "&" + str(self.request.environ['QUERY_STRING'])
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


class TramitacaoAdmCrud(MasterDetailCrud):
    model = TramitacaoAdministrativo
    parent_field = 'documento'
    help_path = ''

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoAdmForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = TramitacaoAdmEditForm

    class ListView(DocumentoAdministrativoMixin, MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao', '-id')

    class DetailView(DocumentoAdministrativoMixin,
                     MasterDetailCrud.DetailView):
        pass


class DocumentoAcessorioAdministrativoCrud(MasterDetailCrud):
    model = DocumentoAcessorioAdministrativo
    parent_field = 'documento'
    help_path = ''

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

    numero_max = DocumentoAdministrativo.objects.filter(
        tipo=tipo, ano=ano).aggregate(Max('numero'))['numero__max']

    return JsonResponse(
        {'numero': numero_max + 1}) if numero_max else JsonResponse(
        {'numero': 1})
