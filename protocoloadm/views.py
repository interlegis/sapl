from datetime import date, datetime
from re import sub

from braces.views import FormValidMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from vanilla import GenericView

from crud import Crud, make_pagination
from materia.models import Proposicao, TipoMateriaLegislativa
from sapl.utils import create_barcode, get_client_ip

from .forms import (AnularProcoloAdmForm, DocumentoAcessorioAdministrativoForm,
                    DocumentoAdministrativoForm, ProposicaoSimpleForm,
                    ProtocoloDocumentForm, ProtocoloForm, ProtocoloMateriaForm,
                    TramitacaoAdmForm)
from .models import (Autor, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, Protocolo,
                     StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)

tipo_documento_administrativo_crud = Crud(TipoDocumentoAdministrativo, '')
documento_administrativo_crud = Crud(DocumentoAdministrativo, '')
documento_acessorio_administrativo_crud = Crud(
    DocumentoAcessorioAdministrativo, '')
status_tramitacao_administrativo_crud = Crud(
    StatusTramitacaoAdministrativo, '')
tramitacao_administrativo_crud = Crud(TramitacaoAdministrativo, '')
protocolo_documento_crud = Crud(Protocolo, '')

# FIXME precisa de uma chave diferente para o layout
protocolo_materia_crud = Crud(Protocolo, '')


class ProtocoloPesquisaView(FormView):
    template_name = 'protocoloadm/protocolo_pesquisa.html'
    form_class = ProtocoloForm
    context_object_name = 'protocolos'
    success_url = reverse_lazy('protocolo')

    def post(self, request, *args, **kwargs):
        form = ProtocoloForm(request.POST or None)

        if form.is_valid():
            kwargs = {}

            if request.POST['tipo_protocolo']:
                kwargs['tipo_protocolo'] = request.POST['tipo_protocolo']

            if request.POST['numero_protocolo']:
                kwargs['numero'] = request.POST['numero_protocolo']

            if request.POST['ano']:
                kwargs['ano'] = request.POST['ano']

            if request.POST['inicial']:
                kwargs['data'] = datetime.strptime(
                    request.POST['inicial'],
                    '%d/%m/%Y').strftime('%Y-%m-%d')

            # if request.POST['final']:
            #     kwargs['final'] = request.POST['final']

            if request.POST['natureza_processo']:
                kwargs['tipo_protocolo'] = request.POST['natureza_processo']

            if request.POST['tipo_documento']:
                kwargs['tipo_documento'] = request.POST['tipo_documento']

            if request.POST['interessado']:
                kwargs['interessado__icontains'] = request.POST['interessado']

            if request.POST['tipo_materia']:
                kwargs['tipo_materia'] = request.POST['tipo_materia']

            if request.POST['autor']:
                kwargs['autor'] = request.POST['autor']

            if request.POST['assunto']:
                kwargs['assunto_ementa__icontains'] = request.POST['assunto']

            request.session['kwargs'] = kwargs
            return redirect('protocolo_list')
        else:
            return self.form_invalid(form)


class ProtocoloListView(ListView):
    template_name = 'protocoloadm/protocolo_list.html'
    context_object_name = 'protocolos'
    model = Protocolo
    paginate_by = 10

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


class AnularProtocoloAdmView(FormView):
    template_name = 'protocoloadm/anular_protocoloadm.html'
    form_class = AnularProcoloAdmForm
    success_url = reverse_lazy('anular_protocolo')
    form_valid_message = _('Protocolo anulado com sucesso!')

    def get_initial(self):
        initial_data = {}
        initial_data['user_anulacao'] = self.request.user.username
        initial_data['ip_anulacao'] = get_client_ip(self.request)
        initial_data['anulado'] = True
        return initial_data

    def post(self, request, *args, **kwargs):

        form = AnularProcoloAdmForm(request.POST)

        if form.is_valid():

            numero = form.cleaned_data['numero']
            ano = form.cleaned_data['ano']

            protocolo = Protocolo.objects.get(numero=numero, ano=ano)
            protocolo.anulado = True
            protocolo.justificativa_anulacao = sub('&nbsp;', ' ', strip_tags(
                            form.cleaned_data['justificativa_anulacao']))
            protocolo.user_anulacao = form.cleaned_data['user_anulacao']
            protocolo.ip_anulacao = form.cleaned_data['ip_anulacao']
            protocolo.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ProtocoloDocumentoView(FormValidMessageMixin, FormView):

    template_name = "protocoloadm/protocolar_documento.html"
    form_class = ProtocoloDocumentForm
    success_url = reverse_lazy('protocolo')
    form_valid_message = _('Protocolo cadastrado com sucesso!')

    def post(self, request, *args, **kwargs):

        form = ProtocoloDocumentForm(request.POST)

        if form.is_valid():
            if form.cleaned_data['numeracao'] == '1':
                numeracao = Protocolo.objects.filter(
                    ano=date.today().year).aggregate(Max('numero'))
            elif form.cleaned_data['numeracao'] == '2':
                numeracao = Protocolo.objects.all().aggregate(Max('numero'))
            # else:
            #     raise ValidationError(_("Campo numeração é obrigatório"))

            if numeracao['numero__max'] is None:
                numeracao['numero__max'] = 0

            protocolo = form.save(commit=False)
            protocolo.numero = numeracao['numero__max'] + 1
            protocolo.ano = datetime.now().year
            protocolo.data = datetime.now().strftime("%Y-%m-%d")
            protocolo.hora = datetime.now().strftime("%H:%M")
            protocolo.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            protocolo.tipo_protocolo = request.POST['tipo_protocolo']
            protocolo.tipo_processo = '0'  # TODO validar o significado
            protocolo.interessado = request.POST['interessado']
            protocolo.anulado = False
            protocolo.tipo_documento = TipoDocumentoAdministrativo.objects.get(
                id=request.POST['tipo_documento'])
            protocolo.assunto_ementa = sub(
                '&nbsp;', ' ', strip_tags(request.POST['assunto']))
            protocolo.numero_paginas = request.POST['num_paginas']
            protocolo.observacao = sub(
                '&nbsp;', ' ', strip_tags(request.POST['observacao']))

            protocolo.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class CriarDocumentoProtocolo(CreateView):
    template_name = "protocoloadm/criar_documento.html"
    form_class = DocumentoAdministrativoForm

    def get_initial(self):
        numero = self.kwargs['pk']
        ano = self.kwargs['ano']
        protocolo = Protocolo.objects.get(ano=ano, numero=numero)
        return self.criar_documento(protocolo)

    def get_success_url(self):
        return reverse('protocolo_mostrar', kwargs={'pk': self.kwargs['pk'],
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
        return doc


class ProtocoloMostrarView(TemplateView):

    template_name = "protocoloadm/protocolo_mostrar.html"

    def get_context_data(self, **kwargs):
        context = super(ProtocoloMostrarView, self).get_context_data(**kwargs)
        numero = self.kwargs['pk']
        ano = self.kwargs['ano']
        protocolo = Protocolo.objects.get(ano=ano, numero=numero)
        context['protocolo'] = protocolo
        return context


class ComprovanteProtocoloView(TemplateView):

    template_name = "protocoloadm/comprovante.html"

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
            autenticacao = str(protocolo.tipo_processo) + \
                protocolo.data.strftime("%Y/%m/%d") + \
                str(protocolo.numero).zfill(6)

        context.update({"protocolo": protocolo,
                        "barcode": barcode,
                        "autenticacao": autenticacao})
        return context


class ProtocoloMateriaView(FormValidMessageMixin, CreateView):

    template_name = "protocoloadm/protocolar_materia.html"
    form_class = ProtocoloMateriaForm
    form_valid_message = _('Matéria cadastrada com sucesso!')

    def post(self, request, *args, **kwargs):

        form = ProtocoloMateriaForm(request.POST)

        if form.is_valid():

            if request.POST['numeracao'] == '1':
                numeracao = Protocolo.objects.filter(
                    ano=date.today().year).aggregate(Max('numero'))
            else:
                numeracao = Protocolo.objects.all().aggregate(Max('numero'))

            if numeracao is None:
                numeracao['numero__max'] = 0

            protocolo = Protocolo()

            protocolo.numero = numeracao['numero__max'] + 1
            protocolo.ano = datetime.now().year
            protocolo.data = datetime.now().strftime("%Y-%m-%d")
            protocolo.hora = datetime.now().strftime("%H:%M")
            protocolo.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            protocolo.tipo_protocolo = request.POST['tipo_protocolo']
            protocolo.tipo_processo = '0'  # TODO validar o significado
            protocolo.autor = Autor.objects.get(id=request.POST['autor'])
            protocolo.anulado = False
            protocolo.tipo_materia = TipoMateriaLegislativa.objects.get(
                id=request.POST['tipo_materia'])
            protocolo.numero_paginas = request.POST['num_paginas']
            protocolo.observacao = sub(
                '&nbsp;', ' ', strip_tags(request.POST['observacao']))

            protocolo.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# TODO: move to Proposicao app


class ProposicaoReceberView(TemplateView):
    template_name = "protocoloadm/proposicao_receber.html"


class ProposicoesNaoRecebidasView(ListView):
    template_name = "protocoloadm/proposicoes_naorecebidas.html"
    model = Proposicao
    paginate_by = 10

    def get_queryset(self):
        return Proposicao.objects.filter(data_envio__isnull=False, status='E')


class ProposicoesNaoIncorporadasView(ListView):
    template_name = "protocoloadm/proposicoes_naoincorporadas.html"
    model = Proposicao
    paginate_by = 10

    def get_queryset(self):
        return Proposicao.objects.filter(data_envio__isnull=False,
                                         data_devolucao__isnull=False,
                                         status='D')


class ProposicoesIncorporadasView(ListView):
    template_name = "protocoloadm/proposicoes_incorporadas.html"
    model = Proposicao
    paginate_by = 10

    def get_queryset(self):
        return Proposicao.objects.filter(data_envio__isnull=False,
                                         data_recebimento__isnull=False,
                                         status='I')


class ProposicaoView(TemplateView):
    template_name = "protocoloadm/proposicoes.html"


class ProposicaoDetailView(DetailView):
    template_name = "protocoloadm/proposicao_view.html"
    model = Proposicao

    def get(self, request, *args, **kwargs):
        proposicao = Proposicao.objects.get(id=kwargs['pk'])
        data = {  # 'ano': proposicao.ano, # TODO: FIX
            'tipo': proposicao.tipo.descricao,  # TODO: FIX
            'materia': proposicao.materia,
            'numero_proposicao': proposicao.numero_proposicao,
            'data_envio': proposicao.data_envio,
            'data_recebimento': proposicao.data_recebimento,
            'descricao': proposicao.descricao}
        form = ProposicaoSimpleForm(initial=data)
        return self.render_to_response({'form': form})

    def get_context_data(self, **kwargs):
        context = super(ProposicaoView, self).get_context_data(**kwargs)
        context['form'] = ProposicaoSimpleForm
        return context


class PesquisarDocumentoAdministrativo(TemplateView):
    template_name = "protocoloadm/pesquisa_doc_adm.html"

    def get_tipos_doc(self):
        return TipoDocumentoAdministrativo.objects.all()

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            {"tipos_doc": TipoDocumentoAdministrativo.objects.all()}
        )

    def post(self, request, *args, **kwargs):

        if request.POST['tipo_documento']:
            kwargs['tipo_id'] = request.POST['tipo_documento']

        if request.POST['numero']:
            kwargs['numero'] = request.POST['numero']

        if request.POST['ano']:
            kwargs['ano'] = request.POST['ano']

        if request.POST['numero_protocolo']:
            kwargs['numero_protocolo'] = request.POST['numero_protocolo']

        if request.POST['periodo_inicial']:
            kwargs['periodo_inicial'] = request.POST['periodo_inicial']

        if request.POST['periodo_final']:
            kwargs['periodo_final'] = request.POST['periodo_final']

        if request.POST['interessado']:
            kwargs['interessado'] = request.POST['interessado']

        if request.POST['assunto']:
            kwargs['assunto_ementa__icontains'] = request.POST['assunto']

        if request.POST['tramitacao']:
            if request.POST['tramitacao'] == 1:
                kwargs['tramitacao'] = True
            elif request.POST['tramitacao'] == 0:
                kwargs['tramitacao'] = False
            else:
                kwargs['tramitacao'] = request.POST['tramitacao']

        # TODO
        # if request.POST['localizacao']:
        #     kwargs['localizacao'] = request.POST['localizacao']

        # if request.POST['situacao']:
        #     kwargs['situacao'] = request.POST['situacao']

        doc = DocumentoAdministrativo.objects.filter(**kwargs)

        if len(doc) == 0:
            return self.render_to_response(
                {'error': _('Nenhum resultado encontrado!'),
                    "tipos_doc": TipoDocumentoAdministrativo.objects.all()}
            )
        else:
            return self.render_to_response(
                {'documentos': doc}
            )


class DetailDocumentoAdministrativo(DetailView):
    template_name = "protocoloadm/detail_doc_adm.html"

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
        return reverse('pesq_doc_adm')

    def get_success_url(self):
        return reverse('detail_doc_adm', kwargs={
            'pk': self.kwargs['pk']})


class DocumentoAcessorioAdministrativoEditView(FormMixin, GenericView):
    template_name = "protocoloadm/documento_acessorio_administrativo_edit.html"

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
        return reverse('doc_ace_adm', kwargs={'pk': pk})


class DocumentoAcessorioAdministrativoView(FormMixin, GenericView):
    template_name = "protocoloadm/documento_acessorio_administrativo.html"

    def get(self, request, *args, **kwargs):
        form = DocumentoAcessorioAdministrativoForm()
        doc = DocumentoAdministrativo.objects.get(
            id=kwargs['pk'])
        doc_ace_null = ''
        doc_acessorio = DocumentoAcessorioAdministrativo.objects.filter(
            documento_id=kwargs['pk'])
        if not doc_acessorio:
            doc_ace_null = _('Nenhum documento acessório \
                 cadastrado para este processo.')

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
        return reverse('doc_ace_adm', kwargs={'pk': pk})


class TramitacaoAdmView(FormMixin, GenericView):
    template_name = "protocoloadm/tramitacao.html"

    def get(self, request, *args, **kwargs):

        pk = kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)
        tramitacoes = TramitacaoAdministrativo.objects.filter(
            documento=documento).order_by('-data_tramitacao')

        return self.render_to_response({'documento': documento,
                                        'tramitacoes': tramitacoes})


class TramitacaoAdmIncluirView(FormMixin, GenericView):
    template_name = "protocoloadm/tramitacao_incluir.html"

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)
        data = {'documento': documento}
        form = TramitacaoAdmForm(initial=data)

        return self.render_to_response({'documento': documento, 'form': form})

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        form = TramitacaoAdmForm(request.POST or None)

        if form.is_valid():
            tramitacao = form.save(commit=False)
            tramitacao.ultima = False
            tramitacao.save()
            return HttpResponseRedirect(
                reverse('tramitacao', kwargs={'pk': pk}))
        else:
            return self.form_invalid(form)


class TramitacaoAdmEditView(FormMixin, GenericView):

    template_name = "protocoloadm/tramitacao_edit.html"

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        tramitacao = TramitacaoAdministrativo.objects.get(id=pk)
        documento = tramitacao.documento
        form = TramitacaoAdmForm(instance=tramitacao)

        return self.render_to_response({'documento': documento, 'form': form})

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        tramitacao = TramitacaoAdministrativo.objects.get(id=pk)
        form = TramitacaoAdmForm(request.POST, instance=tramitacao)

        if form.is_valid():
            tramitacao = form.save(commit=False)
            tramitacao.ultima = False
            tramitacao.save()
            return HttpResponseRedirect(
                reverse('tramitacao', kwargs={'pk': tramitacao.documento.id}))
        else:
            return self.form_invalid(form)


class TramitacaoAdmDeleteView(FormMixin, GenericView):

    template_name = "protocoloadm/tramitacao.html"

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        oid = kwargs['oid']

        documento = DocumentoAdministrativo.objects.get(id=pk)

        tramitacao = TramitacaoAdministrativo.objects.get(id=oid)
        tramitacao.delete()
        tramitacoes = TramitacaoAdministrativo.objects.filter(
            documento=documento)

        return self.render_to_response({'documento': documento,
                                        'tramitacoes': tramitacoes})
