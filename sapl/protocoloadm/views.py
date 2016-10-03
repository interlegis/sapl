from datetime import date, datetime
import json

from braces.views import FormValidMessageMixin
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Max, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, ListView
from django.views.generic.base import TemplateView
from django_filters.views import FilterView

from sapl.base.apps import AppConfig as AppsAppConfig
from sapl.base.models import AppConfig
from sapl.crud.base import (Crud, CrudBaseMixin, CrudCreateView,
                            CrudDeleteView, CrudDetailView, CrudListView,
                            CrudUpdateView, MasterDetailCrud, make_pagination,
                            CrudAux)
from sapl.materia.models import TipoMateriaLegislativa
from sapl.utils import (create_barcode, get_client_ip, permissoes_adm,
                        permissoes_protocoloadm)
import sapl.crud.base

from .forms import (AnularProcoloAdmForm, DocumentoAcessorioAdministrativoForm,
                    DocumentoAdministrativoFilterSet,
                    DocumentoAdministrativoForm, ProtocoloDocumentForm,
                    ProtocoloFilterSet, ProtocoloMateriaForm,
                    TramitacaoAdmEditForm, TramitacaoAdmForm)
from .models import (Autor, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, Protocolo,
                     StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TipoInstituicao,
                     TramitacaoAdministrativo)


TipoDocumentoAdministrativoCrud = CrudAux.build(
    TipoDocumentoAdministrativo, '')
TipoInstituicaoCrud = CrudAux.build(TipoInstituicao, '')


ProtocoloDocumentoCrud = Crud.build(Protocolo, '')
# FIXME precisa de uma chave diferente para o layout
ProtocoloMateriaCrud = Crud.build(Protocolo, '')


DocumentoAcessorioAdministrativoCrud = Crud.build(
    DocumentoAcessorioAdministrativo, '')


class DocumentoAdministrativoMixin:

    def has_permission(self):
        app_config = AppConfig.objects.last()
        if app_config and app_config.documentos_administrativos == 'O':
            return True

        return self.request.user.has_module_perms(AppsAppConfig.label)


class DocumentoAdministrativoCrud(Crud):
    model = DocumentoAdministrativo
    help_path = ''

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data',
                            'numero_protocolo', 'assunto',
                            'interessado', 'tramitacao', 'texto_integral']

    class ListView(Crud.ListView, DocumentoAdministrativoMixin):
        pass

    class DetailView(Crud.DetailView, DocumentoAdministrativoMixin):
        pass


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
    permission_required = permissoes_protocoloadm()

    def get_filterset_kwargs(self, filterset_class):
        super(ProtocoloPesquisaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset().order_by('ano', 'numero')

        qs = qs.distinct()

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
    permission_required = permissoes_protocoloadm()

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
    permission_required = permissoes_protocoloadm()

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
    permission_required = permissoes_protocoloadm()

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def form_valid(self, form):
        f = form.save(commit=False)

        try:
            numeracao = AppConfig.objects.last().sequencia_numeracao
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

        if numero['numero__max'] is None:
            numero['numero__max'] = 0

        f.tipo_processo = '0'  # TODO validar o significado
        f.anulado = False
        f.numero = numero['numero__max'] + 1
        f.ano = datetime.now().year
        f.data = datetime.now().strftime('%Y-%m-%d')
        f.hora = datetime.now().strftime('%H:%M')
        f.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        f.assunto_ementa = self.request.POST['assunto']

        f.save()
        return redirect(self.get_success_url())


class CriarDocumentoProtocolo(PermissionRequiredMixin, CreateView):
    template_name = "protocoloadm/criar_documento.html"
    form_class = DocumentoAdministrativoForm
    permission_required = permissoes_protocoloadm()

    def get_initial(self):
        numero = self.kwargs['pk']
        ano = self.kwargs['ano']
        protocolo = Protocolo.objects.get(ano=ano, numero=numero)
        return self.criar_documento(protocolo)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.kwargs['pk'],
                               'ano': self.kwargs['ano']})

    def criar_documento(self, protocolo):

        numero = Protocolo.objects.filter(
            tipo_documento=protocolo.tipo_documento,
            ano=protocolo.ano,
            anulado=False).aggregate(Max('numero'))

        doc = {}
        doc['tipo'] = protocolo.tipo_documento
        doc['ano'] = protocolo.ano
        doc['data'] = protocolo.data
        doc['numero_protocolo'] = protocolo.numero
        doc['assunto'] = protocolo.assunto_ementa
        doc['interessado'] = protocolo.interessado
        doc['numero'] = numero['numero__max']
        if doc['numero'] is None:
            doc['numero'] = 1
        else:
            doc['numero'] = doc['numero'] + 1
        return doc


class ProtocoloMostrarView(PermissionRequiredMixin, TemplateView):

    template_name = "protocoloadm/protocolo_mostrar.html"
    permission_required = permissoes_protocoloadm()

    def get_context_data(self, **kwargs):
        context = super(ProtocoloMostrarView, self).get_context_data(**kwargs)
        numero = self.kwargs['pk']
        ano = self.kwargs['ano']
        protocolo = Protocolo.objects.get(ano=ano, numero=numero)
        context['protocolo'] = protocolo
        return context


class ComprovanteProtocoloView(PermissionRequiredMixin, TemplateView):

    template_name = "protocoloadm/comprovante.html"
    permission_required = permissoes_protocoloadm()

    def get_context_data(self, **kwargs):
        context = super(ComprovanteProtocoloView, self).get_context_data(
            **kwargs)
        numero = self.kwargs['pk']
        ano = self.kwargs['ano']
        protocolo = Protocolo.objects.get(ano=ano, numero=numero)
        # numero is string, padd with zeros left via .zfill()
        base64_data = create_barcode(numero.zfill(6))
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
    permission_required = permissoes_protocoloadm()

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def form_valid(self, form):
        try:
            numeracao = AppConfig.objects.last().sequencia_numeracao
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

        protocolo.numero = numero['numero__max'] + 1
        protocolo.ano = datetime.now().year
        protocolo.data = datetime.now().strftime("%Y-%m-%d")
        protocolo.hora = datetime.now().strftime("%H:%M")
        protocolo.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        protocolo.tipo_protocolo = self.request.POST['tipo_protocolo']
        protocolo.tipo_processo = '0'  # TODO validar o significado
        if form.cleaned_data['autor']:
            protocolo.autor = form.cleaned_data['autor']
        protocolo.anulado = False
        protocolo.tipo_materia = TipoMateriaLegislativa.objects.get(
            id=self.request.POST['tipo_materia'])
        protocolo.numero_paginas = self.request.POST['numero_paginas']
        protocolo.observacao = self.request.POST['observacao']
        protocolo.save()
        return redirect(self.get_success_url())


class PesquisarDocumentoAdministrativoView(PermissionRequiredMixin,
                                           FilterView,
                                           DocumentoAdministrativoMixin):
    model = DocumentoAdministrativo
    filterset_class = DocumentoAdministrativoFilterSet
    paginate_by = 10
    permission_required = permissoes_adm()

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarDocumentoAdministrativoView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()

        qs = qs.distinct()

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


class DetailDocumentoAdministrativo(PermissionRequiredMixin, DetailView):
    template_name = "protocoloadm/detail_doc_adm.html"
    permission_required = permissoes_adm()

    def get(self, request, *args, **kwargs):
        documento = DocumentoAdministrativo.objects.get(
            id=self.kwargs['pk'])

        form = DocumentoAdministrativoForm(
            instance=documento)
        return self.render_to_response({
            'form': form,
            'pk': kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if 'Salvar' in request.POST:
            form = DocumentoAdministrativoForm(request.POST)

            if form.is_valid():
                doc = form.save(commit=False)
                if 'texto_integral' in request.FILES:
                    doc.texto_integral = request.FILES['texto_integral']
                doc.save()
                return self.form_valid(form)
            else:
                return self.render_to_response({'form': form})
        elif 'Excluir' in request.POST:
            DocumentoAdministrativo.objects.get(
                id=kwargs['pk']).delete()
            return HttpResponseRedirect(self.get_success_delete())

        return HttpResponseRedirect(self.get_success_url())

    def get_success_delete(self):
        return reverse('sapl.protocoloadm:pesq_doc_adm')

    def get_success_url(self):
        return reverse('sapl.protocoloadm:detail_doc_adm', kwargs={
            'pk': self.kwargs['pk']})


class DocumentoAcessorioAdministrativoEditView(PermissionRequiredMixin,
                                               FormView):
    template_name = "protocoloadm/documento_acessorio_administrativo_edit.html"
    permission_required = permissoes_adm()

    def get(self, request, *args, **kwargs):
        doc = DocumentoAdministrativo.objects.get(
            id=kwargs['pk'])
        doc_ace = DocumentoAcessorioAdministrativo.objects.get(
            id=kwargs['ano'])
        form = DocumentoAcessorioAdministrativoForm(instance=doc_ace,
                                                    excluir=True)

        return self.render_to_response({'pk': self.kwargs['pk'],
                                        'doc': doc,
                                        'doc_ace': doc_ace,
                                        'form': form})

    def post(self, request, *args, **kwargs):
        form = DocumentoAcessorioAdministrativoForm(request.POST, excluir=True)
        doc_ace = DocumentoAcessorioAdministrativo.objects.get(
            id=kwargs['ano'])

        if form.is_valid():
            if 'Salvar' in request.POST:
                if 'arquivo' in request.FILES:
                    doc_ace.arquivo = request.FILES['arquivo']
                doc_ace.documento = DocumentoAdministrativo.objects.get(
                    id=kwargs['pk'])
                doc_ace.tipo = TipoDocumentoAdministrativo.objects.get(
                    id=form.data['tipo'])
                doc_ace.nome = form.data['nome']
                doc_ace.autor = form.data['autor']
                doc_ace.data = datetime.strptime(
                    form.data['data'], '%d/%m/%Y')
                doc_ace.assunto = form.data['assunto']

                doc_ace.save()
            elif 'Excluir' in request.POST:
                doc_ace.delete()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.protocoloadm:doc_ace_adm', kwargs={'pk': pk})


class DocumentoAcessorioAdministrativoView(PermissionRequiredMixin, FormView):
    template_name = "protocoloadm/documento_acessorio_administrativo.html"
    permission_required = permissoes_adm()

    def get(self, request, *args, **kwargs):
        form = DocumentoAcessorioAdministrativoForm()
        doc = DocumentoAdministrativo.objects.get(
            id=kwargs['pk'])
        doc_ace_null = ''
        doc_acessorio = DocumentoAcessorioAdministrativo.objects.filter(
            documento_id=kwargs['pk'])
        if not doc_acessorio:
            doc_ace_null = _('Nenhum documento acessório' +
                             'cadastrado para este processo.')

        return self.render_to_response({'pk': kwargs['pk'],
                                        'doc': doc,
                                        'doc_ace': doc_acessorio,
                                        'doc_ace_null': doc_ace_null,
                                        'form': form})

    def post(self, request, *args, **kwargs):
        form = DocumentoAcessorioAdministrativoForm(request.POST)
        if form.is_valid():
            doc_ace = form.save(commit=False)
            if 'arquivo' in request.FILES:
                doc_ace.arquivo = request.FILES['arquivo']
            doc = DocumentoAdministrativo.objects.get(
                id=kwargs['pk'])
            doc_ace.documento = doc
            doc_ace.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.protocoloadm:doc_ace_adm', kwargs={'pk': pk})


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

    class ListView(MasterDetailCrud.ListView, DocumentoAdministrativoMixin):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data_tramitacao', '-id')

    class DetailView(MasterDetailCrud.DetailView,
                     DocumentoAdministrativoMixin):
        pass


def get_nome_autor(request):
    nome_autor = ''
    if request.method == 'GET':
        id = request.GET.get('id', '')
        try:
            autor = Autor.objects.get(pk=id)
            if autor.parlamentar:
                nome_autor = autor.parlamentar.nome_parlamentar
            elif autor.comissao:
                nome_autor = autor.comissao.nome
        except ObjectDoesNotExist:
            pass
    return HttpResponse("{\"nome\":\"" + nome_autor + "\"}",
                        content_type="application/json; charset=utf-8")


def pesquisa_autores(request):
    q = ''
    if request.method == 'GET':
        q = request.GET.get('q', '')

    autor = Autor.objects.filter(
        Q(nome__icontains=q) |
        Q(parlamentar__nome_parlamentar__icontains=q) |
        Q(comissao__nome__icontains=q)
    )

    autores = []

    for a in autor:
        nome = ''
        if a.nome:
            nome = a.nome
        elif a.parlamentar:
            nome = a.parlamentar.nome_parlamentar
        elif a.comissao:
            nome = a.comissao.nome

        autores.append((a.id, nome))

    autores = sorted(autores, key=lambda x: x[1])

    return HttpResponse(json.dumps(autores,
                                   sort_keys=True,
                                   ensure_ascii=False),
                        content_type="application/json; charset=utf-8")
