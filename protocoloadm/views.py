from datetime import date, datetime
from re import sub

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from vanilla import GenericView

import sapl
from crud import build_crud, make_pagination
from materia.models import Proposicao, TipoMateriaLegislativa
from sapl.utils import create_barcode

from .forms import (AnularProcoloAdmForm, DocumentoAcessorioAdministrativoForm,
                    ProposicaoSimpleForm, ProtocoloDocumentForm, ProtocoloForm,
                    ProtocoloMateriaForm, TramitacaoAdmForm)
from .models import (Autor, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, Protocolo,
                     StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)

tipo_documento_administrativo_crud = build_crud(
    TipoDocumentoAdministrativo, '', [

        [_('Tipo Documento Administrativo'),
         [('sigla', 4), ('descricao', 8)]],
    ])

documento_administrativo_crud = build_crud(
    DocumentoAdministrativo, '', [

        [_('Indentificação Básica'),
         [('tipo', 4), ('numero', 4), ('ano', 4)],
            [('data', 6), ('numero_protocolo', 6)],
            [('assunto', 12)],
            [('interessado', 6), ('tramitacao', 6)],
            [('texto_integral', 12)]],

        [_('Outras Informações'),
         [('dias_prazo', 6), ('data_fim_prazo', 6)],
            [('observacao', 12)]],
    ])

documento_acessorio_administrativo_crud = build_crud(
    DocumentoAcessorioAdministrativo, '', [

        [_('Documento Acessório'),
         [('tipo', 4), ('nome', 4), ('data', 4)],
            [('autor', 12)],
            [('arquivo', 12)],
            [('assunto', 12)]],
    ])

status_tramitacao_administrativo_crud = build_crud(
    StatusTramitacaoAdministrativo, '', [

        [_('Status Tramitação Administrativo'),
         [('indicador', 3),
            ('sigla', 2),
            ('descricao', 7)]],
    ])

tramitacao_administrativo_crud = build_crud(
    TramitacaoAdministrativo, '', [

        [_('Tramitação'),
         [('data_tramitacao', 4), ('unidade_tramitacao_local', 8)],
            [('status', 4), ('unidade_tramitacao_destino', 8)],
            [('data_encaminhamento', 6), ('data_fim_prazo', 6)],
            [('texto', 12)]],
    ])

protocolo_documento_crud = build_crud(
    Protocolo, '', [

        [_('Indentificação Documento'),
         [('tipo_protocolo', 12)],
            [('tipo_documento', 6), ('numero_paginas', 6)],
            [('assunto_ementa', 12)],
            [('interessado', 12)],
            [('observacao', 12)]],
    ])

protocolo_materia_crud = build_crud(
    Protocolo, '', [

        [_('Indentificação da Matéria'),
         [('tipo_materia', 6), ('numero_paginas', 6)],
            [('assunto_ementa', 12)],
            [('autor', 12)],
            [('observacao', 12)]],
    ])


class ProtocoloListView(FormMixin, ListView):
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


class ProtocoloPesquisaView(FormMixin, GenericView):
    template_name = 'protocoloadm/protocolo_pesquisa.html'
    form_class = ProtocoloForm()
    context_object_name = 'protocolos'
    paginate_by = 10

    extra_context = {}

    def get_success_url(self):
        return reverse('protocolo')

    def get(self, request, *args, **kwargs):
        form = ProtocoloForm()
        return self.render_to_response({'form': form})

    def get_form(self, data=None, files=None, **kwargs):
        return ProtocoloForm()

    def get_context_data(self, **kwargs):
        context = super(ProtocoloPesquisaView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def post(self, request, *args, **kwargs):
        form = ProtocoloForm(request.POST or None)

        if form.is_valid():
            kwargs = {}

            # format = '%Y-%m-%d'

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


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AnularProtocoloAdmView(FormMixin, GenericView):
    template_name = 'protocoloadm/anular_protocoloadm.html'

    def get_success_url(self):
        return reverse('anular_protocolo')

    def get(self, request, *args, **kwargs):
        form = AnularProcoloAdmForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):

        form = AnularProcoloAdmForm(request.POST)

        if form.is_valid():

            numero = request.POST['numero_protocolo']
            ano = request.POST['ano_protocolo']
            justificativa_anulacao = sub('&nbsp;', ' ', strip_tags(
                request.POST['justificativa_anulacao']))

            user_anulacao = request.user.username
            ip_addr = get_client_ip(request)

            try:
                protocolo = Protocolo.objects.get(numero=numero, ano=ano)

                if protocolo.anulado:
                    errors = form._errors.setdefault(
                        forms.forms.NON_FIELD_ERRORS,
                        forms.util.ErrorList())
                    errors.append("Procolo %s/%s já encontra-se anulado"
                                  % (numero, ano))
                    return self.form_invalid(form)

                protocolo.anulado = True
                protocolo.justificativa_anulacao = justificativa_anulacao
                protocolo.user_anulacao = user_anulacao
                protocolo.ip_anulacao = ip_addr
                protocolo.save()
                return self.form_valid(form)

            except ObjectDoesNotExist:
                errors = form._errors.setdefault(
                    forms.forms.NON_FIELD_ERRORS, forms.util.ErrorList())
                errors.append("Procolo %s/%s não existe" % (numero, ano))
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)


class ProtocoloDocumentoView(FormMixin, GenericView):

    template_name = "protocoloadm/protocolar_documento.html"
    model = Protocolo

    def get_success_url(self):
        return reverse('protocolo')

    def get(self, request, *args, **kwargs):
        form = ProtocoloDocumentForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):

        form = ProtocoloDocumentForm(request.POST)

        if form.is_valid():
            if request.POST['numeracao'] == '1':
                numeracao = Protocolo.objects.filter(
                    ano=date.today().year).aggregate(Max('numero'))
            else:
                numeracao = Protocolo.objects.all().aggregate(Max('numero'))

            if numeracao['numero__max'] is None:
                numeracao['numero__max'] = 0

            protocolo = Protocolo()
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
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ProtocoloMostrarView(TemplateView):

    template_name = "protocoloadm/protocolo_mostrar.html"

    def get(self, request, *args, **kwargs):
        numero = self.kwargs['pk']
        ano = self.kwargs['ano']
        protocolo = Protocolo.objects.get(ano=ano, numero=numero)
        return self.render_to_response({"protocolo": protocolo})


class ComprovanteProtocoloView(TemplateView):

    template_name = "protocoloadm/comprovante.html"

    def get(self, request, *args, **kwargs):
        numero = self.kwargs['pk']
        ano = self.kwargs['ano']
        protocolo = Protocolo.objects.get(ano=ano, numero=numero)
        # numero is string, padd with zeros left via .zfill()
        base64_data = create_barcode(numero.zfill(6))
        barcode = 'data:image/png;base64,{0}'.format(base64_data)

        autenticacao = "** NULO **"

        if not protocolo.anulado:
            autenticacao = str(protocolo.tipo_processo) + \
                           protocolo.data.strftime("%y/%m/%d") + \
                           str(protocolo.numero).zfill(6)

        return self.render_to_response({"protocolo": protocolo,
                                        "barcode": barcode,
                                        "autenticacao": autenticacao})


class ProtocoloMateriaView(FormMixin, GenericView):

    template_name = "protocoloadm/protocolar_materia.html"
    model = Protocolo

    def get(self, request, *args, **kwargs):
        form = ProtocoloMateriaForm()
        return self.render_to_response({'form': form})

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
                {'error': 'Nenhum resultado encontrado!',
                    "tipos_doc": TipoDocumentoAdministrativo.objects.all()}
            )
        else:
            return self.render_to_response(
                {'documentos': doc}
            )


class DetailDocumentoAdministrativo(DetailView):
    template_name = "protocoloadm/detail_doc_adm.html"

    def get_tipos_doc(self):
        return TipoDocumentoAdministrativo.objects.all()

    def get(self, request, *args, **kwargs):
        doc = DocumentoAdministrativo.objects.get(id=kwargs['pk'])
        return self.render_to_response({
            'pk': kwargs['pk'],
            'doc': doc,
            'tipos_doc': TipoDocumentoAdministrativo.objects.all()
        })

    def post(self, request, *args, **kwargs):

        if 'Salvar' in request.POST:
            documento = DocumentoAdministrativo.objects.get(id=kwargs['pk'])

            if request.POST['numero']:
                documento.numero = request.POST['numero']

            if request.POST['ano']:
                documento.ano = request.POST['ano']

            if request.POST['data']:
                documento.data = datetime.strptime(
                    request.POST['data'], "%d/%m/%Y")

            if request.POST['numero_protocolo']:
                documento.numero_protocolo = request.POST['numero_protocolo']

            if request.POST['assunto']:
                documento.assunto = request.POST['assunto']

            if request.POST['interessado']:
                documento.interessado = request.POST['interessado']

            if request.POST['tramitacao']:
                documento.tramitacao = request.POST['tramitacao']

            if request.POST['dias_prazo']:
                documento.dias_prazo = request.POST['dias_prazo']

            if request.POST['data_fim_prazo']:
                documento.data_fim_prazo = datetime.strptime(
                    request.POST['data_fim_prazo'], "%d/%m/%Y")

            if request.POST['observacao']:
                documento.observacao = request.POST['observacao']

            documento.save()
        elif 'Excluir' in request.POST:
            DocumentoAdministrativo.objects.get(
                id=kwargs['pk']).delete()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('pesq_doc_adm')


class DocumentoAcessorioAdministrativoView(FormMixin, GenericView):
    template_name = "protocoloadm/documento_acessorio_administrativo.html"

    def get(self, request, *args, **kwargs):
        form = DocumentoAcessorioAdministrativoForm()
        doc = DocumentoAdministrativo.objects.get(
            id=kwargs['pk'])
        doc_ace_null = ''
        try:
            doc_acessorio = DocumentoAcessorioAdministrativo.objects.filter(
                documento_id=kwargs['pk'])
        except ObjectDoesNotExist:
            doc_ace_null = 'Nenhum documento acessório \
                 cadastrado para este processo.'

        return self.render_to_response({'pk': kwargs['pk'],
                                        'doc': doc,
                                        'doc_ace': doc_acessorio,
                                        'doc_ace_null': doc_ace_null,
                                        'form': form})

    def post(self, request, *args, **kwargs):
        form = DocumentoAcessorioAdministrativoForm(request.POST)
        if form.is_valid():
            doc_acessorio = DocumentoAcessorioAdministrativo()
            doc_acessorio.tipo = form.cleaned_data['tipo']
            doc_acessorio.nome = form.cleaned_data['nome']
            doc_acessorio.data = form.cleaned_data['data']
            doc_acessorio.autor = form.cleaned_data['autor']
            doc_acessorio.assunto = form.cleaned_data['assunto']
            doc_acessorio.arquivo = request.FILES['arquivo']
            doc_acessorio.documento = DocumentoAdministrativo.objects.get(
                id=kwargs['pk'])
            doc_acessorio.save()

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
