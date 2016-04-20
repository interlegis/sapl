import os
from datetime import datetime
from random import choice
from string import ascii_letters, digits

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, FormView, ListView, TemplateView
from django_filters.views import FilterView

import crud.base
from base.models import CasaLegislativa
from comissoes.models import Comissao, Composicao
from compilacao.views import IntegracaoTaView
from crud.base import Crud, make_pagination
from norma.models import LegislacaoCitada, NormaJuridica, TipoNormaJuridica
from parlamentares.models import Partido
from sapl.utils import get_base_url

from .forms import (AcompanhamentoMateriaForm, AutoriaForm,
                    DespachoInicialForm, DocumentoAcessorioForm,
                    LegislacaoCitadaForm, MateriaAnexadaForm,
                    MateriaLegislativaFilterSet, NumeracaoForm, ProposicaoForm,
                    RelatoriaForm, TramitacaoForm, filtra_tramitacao_destino,
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
AutoriaCrud = Crud.build(Autoria, '')
DocumentoAcessorioCrud = Crud.build(DocumentoAcessorio, '')
NumeracaoCrud = Crud.build(Numeracao, '')
OrgaoCrud = Crud.build(Orgao, 'orgao')
RelatoriaCrud = Crud.build(Relatoria, '')
TipoProposicaoCrud = Crud.build(TipoProposicao, 'tipo_proposicao')
ProposicaoCrud = Crud.build(Proposicao, '')
StatusTramitacaoCrud = Crud.build(StatusTramitacao, 'status_tramitacao')
UnidadeTramitacaoCrud = Crud.build(UnidadeTramitacao, 'unidade_tramitacao')
TramitacaoCrud = Crud.build(Tramitacao, '')


class MateriaLegislativaCrud(Crud):
    model = MateriaLegislativa
    help_path = 'materia_legislativa'

    class BaseMixin(crud.base.CrudBaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data_apresentacao']


class MateriaAnexadaView(FormView):
    template_name = "materia/materia_anexada.html"
    form_class = MateriaAnexadaForm
    form_valid_message = _('Matéria anexada com sucesso!')

    def get(self, request, *args, **kwargs):
        form = MateriaAnexadaForm()
        materia = MateriaLegislativa.objects.get(
            id=kwargs['pk'])
        anexadas = Anexada.objects.filter(
            materia_principal_id=kwargs['pk'])

        return self.render_to_response({'object': materia,
                                        'anexadas': anexadas,
                                        'form': form})

    def form_invalid(self,
                     form,
                     request,
                     mat_principal,
                     anexadas,
                     msg='Erro ineseperado.'):
        messages.add_message(request, messages.ERROR, msg)
        return self.render_to_response(
            {'form': form,
             'object': mat_principal,
             'anexadas': anexadas})

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        anexadas = Anexada.objects.filter(
            materia_principal_id=kwargs['pk'])
        mat_principal = MateriaLegislativa.objects.get(
            id=kwargs['pk'])

        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            numero = form.cleaned_data['numero']
            ano = form.cleaned_data['ano']
            data_anexacao = form.cleaned_data['data_anexacao']
            data_desanexacao = form.cleaned_data['data_desanexacao']

            try:
                mat_anexada = MateriaLegislativa.objects.get(
                    numero=numero, ano=ano, tipo=tipo)

                if mat_principal.tipo == mat_anexada.tipo:
                    msg = _('A matéria a ser anexada não pode ser do mesmo'
                            ' tipo da matéria principal.')
                    self.form_invalid(
                        form, request, mat_principal, anexadas, msg)
                anexada = Anexada()
                anexada.materia_principal = mat_principal
                anexada.materia_anexada = mat_anexada
                anexada.data_anexacao = data_anexacao
                if data_desanexacao:
                    anexada.data_desanexacao = data_desanexacao

                anexada.save()
            except ObjectDoesNotExist:
                msg = _('A matéria a ser anexada não existe no cadastro'
                        ' de matérias legislativas.')
                self.form_invalid(form, request, mat_principal, anexadas, msg)
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'object': mat_principal,
                 'anexadas': anexadas})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:materia_anexada', kwargs={'pk': pk})


class MateriaAnexadaEditView(FormView):
    template_name = "materia/materia_anexada_edit.html"
    form_class = MateriaAnexadaForm

    def form_invalid(self,
                     form,
                     request,
                     mat_principal,
                     msg='Erro ineseperado.'):
        messages.add_message(request, messages.ERROR, msg)
        return self.render_to_response(
            {'form': form, 'object': mat_principal})

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        anexada = Anexada.objects.get(id=kwargs['id'])

        data = {}
        data['tipo'] = anexada.materia_anexada.tipo
        data['numero'] = anexada.materia_anexada.numero
        data['ano'] = anexada.materia_anexada.ano
        data['data_anexacao'] = anexada.data_anexacao
        data['data_desanexacao'] = anexada.data_desanexacao

        form = MateriaAnexadaForm(initial=data, excluir=True)

        return self.render_to_response(
            {'object': materia,
             'form': form})

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        anexada = Anexada.objects.get(id=kwargs['id'])
        mat_principal = MateriaLegislativa.objects.get(
            id=kwargs['pk'])
        if form.is_valid():
            if 'Excluir' in request.POST:
                anexada.delete()
                return self.form_valid(form)
            elif 'salvar' in request.POST:

                tipo = form.cleaned_data['tipo']
                numero = form.cleaned_data['numero']
                ano = form.cleaned_data['ano']
                data_anexacao = form.cleaned_data['data_anexacao']

                if 'data_desanexacao' in request.POST:
                    data_desanexacao = form.cleaned_data['data_desanexacao']

                try:
                    mat_anexada = MateriaLegislativa.objects.get(
                        numero=numero, ano=ano, tipo=tipo)

                    if mat_principal.tipo == mat_anexada.tipo:
                        msg = _('A matéria a ser anexada não pode ser do mesmo \
                        tipo da matéria principal.')
                        self.form_invalid(form, request, mat_principal, msg)

                    anexada.materia_principal = mat_principal
                    anexada.materia_anexada = mat_anexada
                    anexada.data_anexacao = data_anexacao

                    if data_desanexacao:
                        anexada.data_desanexacao = data_desanexacao

                    anexada.save()
                    return self.form_valid(form)

                except ObjectDoesNotExist:
                    msg = _('A matéria a ser anexada não existe no cadastro \
                        de matérias legislativas.')
                    self.form_invalid(form, request, mat_principal, msg)
        else:
            return self.render_to_response(
                {'form': form,
                 'materia': mat_principal})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia_anexada', kwargs={'pk': pk})


class DespachoInicialView(CreateView):
    template_name = "materia/despacho_inicial.html"
    form_class = DespachoInicialForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.filter(materia_id=materia.id)
        form = DespachoInicialForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'despachos': despacho})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.filter(materia_id=materia.id)

        if form.is_valid():
            despacho = DespachoInicial()
            despacho.comissao = form.cleaned_data['comissao']
            despacho.materia = materia
            despacho.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'despachos': despacho})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:despacho_inicial', kwargs={'pk': pk})


class DespachoInicialEditView(CreateView):
    template_name = "materia/despacho_inicial_edit.html"
    form_class = DespachoInicialForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.get(id=kwargs['id'])
        form = DespachoInicialForm(instance=despacho, excluir=True)

        return self.render_to_response({'object': materia, 'form': form})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        despacho = DespachoInicial.objects.get(id=kwargs['id'])

        if form.is_valid():
            if 'Excluir' in request.POST:
                despacho.delete()
            elif 'salvar' in request.POST:
                despacho.comissao = form.cleaned_data['comissao']
                despacho.materia = materia
                despacho.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'despacho': despacho,
                 'comissoes': Comissao.objects.all()})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:despacho_inicial', kwargs={'pk': pk})


class LegislacaoCitadaView(FormView):
    template_name = "materia/legislacao_citada.html"
    form_class = LegislacaoCitadaForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao = LegislacaoCitada.objects.filter(materia_id=kwargs['pk'])
        form = LegislacaoCitadaForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'legislacao': legislacao})

    def post(self, request, *args, **kwargs):
        form = LegislacaoCitadaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao_list = LegislacaoCitada.objects.filter(
            materia_id=kwargs['pk'])

        if form.is_valid():
            legislacao = LegislacaoCitada()

            try:
                norma = NormaJuridica.objects.get(
                    tipo_id=form.cleaned_data['tipo'],
                    numero=form.cleaned_data['numero'],
                    ano=form.cleaned_data['ano'])
            except ObjectDoesNotExist:
                msg = _('Norma Juridica não existe.')
                messages.add_message(request, messages.INFO, msg)
                return self.render_to_response({'form': form,
                                                'object': materia,
                                                'legislacao': legislacao_list})
            legislacao.materia = materia
            legislacao.norma = norma
            legislacao.disposicoes = form.cleaned_data['disposicoes']
            legislacao.parte = form.cleaned_data['parte']
            legislacao.livro = form.cleaned_data['livro']
            legislacao.titulo = form.cleaned_data['titulo']
            legislacao.capitulo = form.cleaned_data['capitulo']
            legislacao.secao = form.cleaned_data['secao']
            legislacao.subsecao = form.cleaned_data['subsecao']
            legislacao.artigo = form.cleaned_data['artigo']
            legislacao.paragrafo = form.cleaned_data['paragrafo']
            legislacao.inciso = form.cleaned_data['inciso']
            legislacao.alinea = form.cleaned_data['alinea']
            legislacao.item = form.cleaned_data['item']

            legislacao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'legislacao': legislacao_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:legislacao_citada', kwargs={'pk': pk})


class LegislacaoCitadaEditView(FormView):
    template_name = "materia/legislacao_citada_edit.html"
    form_class = LegislacaoCitadaForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:legislacao_citada', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao = LegislacaoCitada.objects.get(id=kwargs['id'])
        form = LegislacaoCitadaForm()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'legislacao': legislacao,
             'tipos_norma': TipoNormaJuridica.objects.all()})

    def post(self, request, *args, **kwargs):
        form = LegislacaoCitadaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        legislacao = LegislacaoCitada.objects.get(id=kwargs['id'])

        if form.is_valid():
            if 'excluir' in request.POST:
                legislacao.delete()
                return self.form_valid(form)
            elif 'salvar' in request.POST:
                try:
                    norma = NormaJuridica.objects.get(
                        tipo_id=form.cleaned_data['tipo'],
                        numero=form.cleaned_data['numero'],
                        ano=form.cleaned_data['ano'])
                except ObjectDoesNotExist:
                    msg = _('Norma Juridica não existe.')
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'form': form,
                         'object': materia,
                         'legislacao': legislacao,
                         'tipos_norma': TipoNormaJuridica.objects.all()})
                legislacao.materia = materia
                legislacao.norma = norma
                legislacao.disposicoes = form.cleaned_data['disposicoes']
                legislacao.parte = form.cleaned_data['parte']
                legislacao.livro = form.cleaned_data['livro']
                legislacao.titulo = form.cleaned_data['titulo']
                legislacao.capitulo = form.cleaned_data['capitulo']
                legislacao.secao = form.cleaned_data['secao']
                legislacao.subsecao = form.cleaned_data['subsecao']
                legislacao.artigo = form.cleaned_data['artigo']
                legislacao.paragrafo = form.cleaned_data['paragrafo']
                legislacao.inciso = form.cleaned_data['inciso']
                legislacao.alinea = form.cleaned_data['alinea']
                legislacao.item = form.cleaned_data['item']

                legislacao.save()
                return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'object': materia})


class NumeracaoView(CreateView):
    template_name = "materia/numeracao.html"
    form_class = NumeracaoForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao = Numeracao.objects.filter(materia_id=kwargs['pk'])

        return self.render_to_response(
            {'object': materia,
             'form': self.get_form(),
             'numeracao': numeracao})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao_list = Numeracao.objects.filter(
            materia_id=kwargs['pk'])

        if form.is_valid():
            numeracao = form.save(commit=False)
            numeracao.materia = materia
            numeracao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'numeracao': numeracao_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:numeracao', kwargs={'pk': pk})


class NumeracaoEditView(CreateView):
    template_name = "materia/numeracao_edit.html"
    form_class = NumeracaoForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao = Numeracao.objects.get(id=kwargs['id'])
        form = NumeracaoForm(instance=numeracao, excluir=True)

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'numeracao': numeracao})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        numeracao = Numeracao.objects.get(id=kwargs['id'])

        if form.is_valid():
            if 'excluir' in request.POST:
                numeracao.delete()
            elif 'salvar' in request.POST:
                numeracao.materia = materia
                numeracao.tipo_materia = form.cleaned_data['tipo_materia']
                numeracao.numero_materia = form.cleaned_data['numero_materia']
                numeracao.ano_materia = form.cleaned_data['ano_materia']
                numeracao.data_materia = form.cleaned_data['data_materia']
                numeracao.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'numeracao': numeracao})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:numeracao', kwargs={'pk': pk})


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


class DocumentoAcessorioEditView(CreateView):
    template_name = "materia/documento_acessorio_edit.html"
    form_class = DocumentoAcessorioForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        documento = DocumentoAcessorio.objects.get(id=kwargs['id'])
        form = DocumentoAcessorioForm(instance=documento, excluir=True)
        return self.render_to_response({'object': materia, 'form': form})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        documento = DocumentoAcessorio.objects.get(id=kwargs['id'])
        if form.is_valid():
            if 'Excluir' in request.POST:
                documento.delete()
            elif 'salvar' in request.POST:
                documento.materia = materia
                documento.tipo = form.cleaned_data['tipo']
                documento.data = form.cleaned_data['data']
                documento.nome = form.cleaned_data['nome']
                documento.autor = form.cleaned_data['autor']
                documento.ementa = form.cleaned_data['ementa']
                documento.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'doc': documento})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:documento_acessorio', kwargs={'pk': pk})


class RelatoriaEditView(FormView):
    template_name = "materia/relatoria_edit.html"
    form_class = RelatoriaForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:relatoria', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        form = RelatoriaForm()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        relatoria = Relatoria.objects.get(
            id=kwargs['id'])
        composicao = Composicao.objects.filter(
            comissao=relatoria.comissao).last()
        parlamentares = composicao.participacao_set.all()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'relatoria': relatoria,
             'tipo_fim_relatorias': TipoFimRelatoria.objects.all(),
             'parlamentares': parlamentares})

    def post(self, request, *args, **kwargs):
        form = RelatoriaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        relatoria = Relatoria.objects.get(id=kwargs['id'])
        composicao = Composicao.objects.filter(
            comissao=relatoria.comissao).last()
        parlamentares = composicao.participacao_set.all()

        if form.is_valid():
            if 'excluir' in request.POST:
                relatoria.delete()
                return self.form_valid(form)
            elif 'salvar' in request.POST:
                relatoria.materia = materia
                relatoria.comissao = relatoria.comissao
                relatoria.data_designacao_relator = form.cleaned_data[
                    'data_designacao_relator']
                relatoria.data_destituicao_relator = form.cleaned_data[
                    'data_destituicao_relator']
                relatoria.parlamentar = form.cleaned_data['parlamentar']
                relatoria.tipo_fim_relatoria = form.cleaned_data[
                    'tipo_fim_relatoria']
                relatoria.save()
                return self.form_valid(form)
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'relatoria': relatoria,
                 'tipo_fim_relatorias': TipoFimRelatoria.objects.all(),
                 'parlamentares': parlamentares})


class RelatoriaView(FormView):
    template_name = "materia/relatoria.html"
    form_class = RelatoriaForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:relatoria', kwargs={'pk': pk})

    def post(self, request, *args, **kwargs):
        form = RelatoriaForm(request.POST)
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])

        if not materia.tramitacao_set.all():
            msg = _(
                'Adicione alguma Tramitação antes de adicionar uma Comissão!')
            messages.add_message(request, messages.INFO, msg)
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'tipo_fim_relatoria': TipoFimRelatoria.objects.all()
                 })
        else:
            relatorias = Relatoria.objects.filter(
                materia_id=kwargs['pk']).order_by(
                    '-data_designacao_relator')
            localizacao = Tramitacao.objects.filter(
                materia=materia).last()

            comissao = Comissao.objects.get(
                id=localizacao.unidade_tramitacao_destino.comissao.id)

            if form.is_valid():
                relatoria = form.save(commit=False)
                relatoria.materia = materia
                relatoria.comissao = comissao
                relatoria.save()
                return self.form_valid(form)
            else:
                try:
                    composicao = Composicao.objects.get(comissao=comissao)
                except ObjectDoesNotExist:
                    msg = _('Não há composição nesta Comissão!')
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'object': materia,
                         'form': form,
                         'relatorias': relatorias,
                         'comissao': comissao})

                parlamentares = composicao.participacao_set.all()

                return self.render_to_response(
                    {'object': materia,
                     'form': form,
                     'relatorias': relatorias,
                     'comissao': comissao,
                     'tipo_fim_relatoria': TipoFimRelatoria.objects.all(),
                     'parlamentares': parlamentares})

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        relatorias = Relatoria.objects.filter(
            materia_id=kwargs['pk']).order_by('-data_designacao_relator')
        form = RelatoriaForm()

        localizacao = Tramitacao.objects.filter(
            materia=materia).last()

        if not materia.tramitacao_set.all():
            msg = _(
                'Adicione alguma Tramitação antes de adicionar uma Comissão!')
            messages.add_message(request, messages.INFO, msg)
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'relatorias': relatorias,
                 'tipo_fim_relatoria': TipoFimRelatoria.objects.all()
                 })
        elif not localizacao.unidade_tramitacao_destino.comissao:
            msg = _('O local atual deve  ser uma Comissão!')
            messages.add_message(request, messages.INFO, msg)
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'relatorias': relatorias})
        else:
            try:
                comissao = Comissao.objects.get(
                    id=localizacao.unidade_tramitacao_destino.comissao.id)
                composicao = Composicao.objects.filter(
                    comissao=comissao).last()
                if not composicao:
                    msg = _('Não há composição nesta Comissão!')
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'object': materia,
                         'form': form,
                         'relatorias': relatorias,
                         'comissao': comissao})
                parlamentares = composicao.participacao_set.all()
            except ObjectDoesNotExist:
                msg = _('O local atual deve  ser uma Comissão!')
                messages.add_message(request, messages.INFO, msg)
                return self.render_to_response(
                    {'object': materia,
                     'form': form,
                     'relatorias': relatorias})
            else:
                composicao = Composicao.objects.filter(
                    comissao=comissao).last()
                parlamentares = composicao.participacao_set.all()
                return self.render_to_response(
                    {'object': materia,
                     'form': form,
                     'relatorias': relatorias,
                     'comissao': comissao,
                     'tipo_fim_relatoria': TipoFimRelatoria.objects.all(),
                     'parlamentares': parlamentares})


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
    materia_url = reverse('materia:acompanhar_materia',
                          kwargs={'pk': materia.id})
    confirmacao_url = reverse('materia:acompanhar_confirmar',
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
    url_materia = reverse('materia:acompanhar_materia',
                          kwargs={'pk': materia.id})
    url_excluir = reverse('materia:acompanhar_excluir',
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


class TramitacaoView(CreateView):
    template_name = "materia/tramitacao.html"
    form_class = TramitacaoForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacoes = Tramitacao.objects.filter(
            materia_id=kwargs['pk']).order_by('-data_tramitacao')
        form = self.get_form()

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'tramitacoes': tramitacoes})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacoes_list = Tramitacao.objects.filter(
            materia_id=kwargs['pk']).order_by('-data_tramitacao')

        if form.is_valid():
            ultima_tramitacao = Tramitacao.objects.filter(
                materia_id=kwargs['pk']).last()
            if ultima_tramitacao:
                destino = ultima_tramitacao.unidade_tramitacao_destino
                cleaned_data = form.cleaned_data['unidade_tramitacao_local']
                if (destino == cleaned_data):
                    tramitacao = form.save(commit=False)
                    tramitacao.materia = materia
                    tramitacao.save()
                else:
                    msg = _('A origem da nova tramitação \
                            deve ser igual ao destino da última adicionada!')
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'form': form,
                         'object': materia,
                         'tramitacoes': tramitacoes_list})

                    do_envia_email_tramitacao(request, materia)
            else:
                tramitacao = form.save(commit=False)
                tramitacao.materia = materia
                tramitacao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form,
                                            'object': materia,
                                            'tramitacoes': tramitacoes_list})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:tramitacao_materia', kwargs={'pk': pk})


class TramitacaoEditView(CreateView):
    template_name = "materia/tramitacao_edit.html"
    form_class = TramitacaoForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacao = Tramitacao.objects.get(id=kwargs['id'])
        form = TramitacaoForm(excluir=True, instance=tramitacao)

        return self.render_to_response(
            {'object': materia,
             'form': form,
             'tramitacao': tramitacao})

    def post(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        tramitacao = Tramitacao.objects.get(id=kwargs['id'])
        form = self.get_form()

        if form.is_valid():
            if 'excluir' in request.POST:
                if tramitacao == Tramitacao.objects.filter(
                        materia=materia).last():
                    tramitacao.delete()
                else:
                    msg = _('Somente a útlima tramitação pode ser deletada!')
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response(
                        {'object': materia,
                         'form': form,
                         'tramitacao': tramitacao})
            elif 'salvar' in request.POST:
                tramitacao.status = form.cleaned_data['status']
                tramitacao.turno = form.cleaned_data['turno']
                tramitacao.urgente = form.cleaned_data['urgente']
                tramitacao.unidade_tramitacao_destino = form.cleaned_data[
                    'unidade_tramitacao_destino']
                tramitacao.data_encaminhamento = form.cleaned_data[
                    'data_encaminhamento']
                tramitacao.data_fim_prazo = form.cleaned_data['data_fim_prazo']
                tramitacao.texto = form.cleaned_data['texto']

                tramitacao.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form,
                 'tramitacao': tramitacao})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:tramitacao_materia', kwargs={'pk': pk})


class AutoriaView(CreateView):
    template_name = "materia/autoria.html"
    form_class = AutoriaForm
    form_valid_message = _('Autoria cadastrada com sucesso!')
    model = Autoria

    def get_initial(self):
        initial = super(AutoriaView, self).get_initial()
        initial['materia_id'] = self.kwargs['pk']
        return initial

    def get_context_data(self, **kwargs):
        context = super(AutoriaView, self).get_context_data(**kwargs)

        materia = MateriaLegislativa.objects.get(id=self.kwargs['pk'])
        autorias = Autoria.objects.filter(materia=materia)

        context.update({'object': materia,
                        'autorias': autorias})
        return context

    def form_valid(self, form):
        materia = MateriaLegislativa.objects.get(id=form.data['materia_id'])
        if 'salvar' in self.request.POST:
            autoria = Autoria()
            autoria.autor = Autor.objects.get(id=form.data['autor'])
            autoria.materia = materia
            autoria.primeiro_autor = form.data['primeiro_autor']

            if form.data['partido']:
                filiacao_autor = Partido.objects.get(id=form.data['partido'])
                autoria.partido = filiacao_autor

            autoria.save()

        return redirect(self.get_success_url())

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:autoria', kwargs={'pk': pk})


class AutoriaEditView(CreateView):
    template_name = "materia/autoria_edit.html"
    form_class = AutoriaForm

    def get(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        autoria = Autoria.objects.get(id=self.kwargs['id'])
        form = AutoriaForm(instance=autoria, excluir=True)

        return self.render_to_response(
            {'object': materia,
             'form': form})

    def post(self, request, *args, **kwargs):
        materia = MateriaLegislativa.objects.get(id=kwargs['pk'])
        form = self.get_form()
        if form.is_valid():
            autoria = Autoria.objects.get(id=self.kwargs['id'])
            if 'salvar' in request.POST:
                autoria.autor = Autor.objects.get(id=form.data['autor'])
                autoria.primeiro_autor = form.data['primeiro_autor']
                if 'partido' in form.data:
                    autoria.partido = Partido.objects.get(
                        id=form.data['partido'])
                autoria.materia = materia
                autoria.save()
            elif 'Excluir' in request.POST:
                autoria.delete()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'object': materia,
                 'form': form})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('materia:autoria', kwargs={'pk': pk})


class ProposicaoListView(ListView):
    template_name = "materia/proposicao/proposicao_list.html"
    paginate_by = 10
    model = Proposicao

    def get_queryset(self):
        return Proposicao.objects.all().order_by('data_envio',
                                                 'tipo',
                                                 'descricao')

    def get_context_data(self, **kwargs):
        context = super(ProposicaoListView, self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        return context


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


class ProposicaoView(CreateView):
    template_name = "materia/proposicao/proposicao.html"
    form_class = ProposicaoForm

    def get_success_url(self):
        return reverse('materia:list_proposicao')

    def get(self, request, *args, **kwargs):
        return self.render_to_response({'form': self.get_form()})

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            proposicao = form.save(commit=False)
            tipo = TipoProposicao.objects.get(id=form.data['tipo'])
            if tipo.descricao == 'Parecer':
                try:
                    materia = MateriaLegislativa.objects.get(
                        tipo_id=int(form.data['tipo_materia']),
                        ano=int(form.data['ano_materia']),
                        numero=int(form.data['numero_materia']))
                except ObjectDoesNotExist:
                    msg = _('Matéria adicionada não existe!')
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response({'form': form})
                else:
                    proposicao.autor = materia.autoria_set.first().autor
                    proposicao.materia = materia
            proposicao.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response({'form': form})


class ProposicaoEditView(CreateView):
    template_name = "materia/proposicao/proposicao.html"
    form_class = ProposicaoForm

    def get_success_url(self):
        return reverse('materia:list_proposicao')

    def get(self, request, *args, **kwargs):
        proposicao = Proposicao.objects.get(id=kwargs['pk'])
        return self.render_to_response({'form': ProposicaoForm(
            excluir=True,
            instance=proposicao)})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        proposicao = Proposicao.objects.get(id=kwargs['pk'])
        if form.is_valid():
            if 'Excluir' in request.POST:
                if proposicao.data_envio:
                    proposicao.data_envio = None
                    proposicao.save()
                else:
                    proposicao.delete()
            if 'salvar' or "remover-foto" in request.POST:
                if 'texto_original' in request.FILES:
                    # if os.unlink(proposicao.texto_original.path):
                    #     proposicao.texto_original = None
                    proposicao.texto_original = request.FILES['texto_original']
                tipo = TipoProposicao.objects.get(id=form.data['tipo'])
                proposicao.tipo = tipo
                proposicao.descricao = form.data['descricao']
                if tipo.descricao == 'Parecer':
                    try:
                        materia = MateriaLegislativa.objects.get(
                            tipo_id=int(form.data['tipo_materia']),
                            ano=int(form.data['ano_materia']),
                            numero=int(form.data['numero_materia']))
                    except ObjectDoesNotExist:
                        msg = _('Matéria adicionada não existe!')
                        messages.add_message(request, messages.INFO, msg)
                        return self.render_to_response({'form': form})
                    else:
                        proposicao.autor = materia.autoria_set.first().autor
                        proposicao.materia = materia
                if not proposicao.data_envio:
                    proposicao.data_envio = datetime.now()
                if "remover-texto" in request.POST:
                    try:
                        os.unlink(proposicao.texto_original.path)
                    except OSError:
                        pass  # Should log this error!!!!!
                    proposicao.texto_original = None
                proposicao.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response({'form': form})


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
