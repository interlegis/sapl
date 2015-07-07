# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from materia.models import Autor, TipoMateriaLegislativa, UnidadeTramitacao


class TipoDocumentoAdministrativo(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_(u'Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))

    class Meta:
        verbose_name = _(u'Tipo de Documento Administrativo')
        verbose_name_plural = _(u'Tipos de Documento Administrativo')


class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(TipoDocumentoAdministrativo, verbose_name=_(u'Tipo Documento'))
    numero = models.IntegerField(verbose_name=_(u'Número'))
    ano = models.SmallIntegerField(verbose_name=_(u'Ano'))
    data = models.DateField(verbose_name=_(u'Data'))
    numero_protocolo = models.IntegerField(blank=True, null=True, verbose_name=_(u'Núm. Protocolo'))
    interessado = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True)
    dias_prazo = models.IntegerField(blank=True, null=True, verbose_name=_(u'Dias Prazo'))
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim Prazo'))
    tramitacao = models.BooleanField(verbose_name=_(u'Em Tramitação?'))
    assunto = models.TextField(verbose_name=_(u'Assunto'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))

    class Meta:
        verbose_name = _(u'Documento Administrativo')
        verbose_name_plural = _(u'Documentos Administrativos')


class DocumentoAcessorioAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo)
    tipo = models.ForeignKey(TipoDocumentoAdministrativo, verbose_name=_(u'Tipo'))
    nome = models.CharField(max_length=30, verbose_name=_(u'Nome'))
    arquivo = models.CharField(max_length=100, verbose_name=_(u'Arquivo'))
    data = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))
    autor = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Autor'))
    assunto = models.TextField(blank=True, null=True, verbose_name=_(u'Assunto'))
    indexacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _(u'Documento Acessório')
        verbose_name_plural = _(u'Documentos Acessórios')


class Protocolo(models.Model):
    numero = models.IntegerField(blank=True, null=True, verbose_name=_(u'Número do Protocolo'))
    ano = models.SmallIntegerField()
    data = models.DateField()
    hora = models.TimeField()
    timestamp = models.DateTimeField()
    tipo_protocolo = models.IntegerField(verbose_name=_(u'Tipo de Protocolo'))
    tipo_processo = models.IntegerField()
    interessado = models.CharField(max_length=60, blank=True, null=True, verbose_name=_(u'Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True)
    assunto_ementa = models.TextField(blank=True, null=True)
    tipo_documento = models.ForeignKey(TipoDocumentoAdministrativo, blank=True, null=True, verbose_name=_(u'Tipo de documento'))
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True, verbose_name=_(u'Tipo Matéria'))
    numero_paginas = models.IntegerField(blank=True, null=True, verbose_name=_(u'Número de Páginas'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))
    anulado = models.BooleanField()
    user_anulacao = models.CharField(max_length=20, blank=True, null=True)
    ip_anulacao = models.CharField(max_length=15, blank=True, null=True)
    justificativa_anulacao = models.CharField(max_length=60, blank=True, null=True)
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _(u'Protocolo')
        verbose_name_plural = _(u'Protocolos')


class StatusTramitacaoAdministrativo(models.Model):
    FIM = 'F'
    RETORNO = 'R'
    INDICADOR_CHOICES = ((FIM, _(u'Fim')),
                         (RETORNO, _(u'Retorno')))

    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))
    descricao = models.CharField(max_length=60, verbose_name=_(u'Descrição'))
    # TODO make specific migration considering both ind_fim_tramitacao, ind_retorno_tramitacao
    indicador = models.CharField(max_length=1, verbose_name=_(u'Indicador da Tramitação'), choices=INDICADOR_CHOICES)

    class Meta:
        verbose_name = _(u'Status de Tramitação')
        verbose_name_plural = _(u'Status de Tramitação')


class TramitacaoAdministrativo(models.Model):
    status = models.ForeignKey(StatusTramitacaoAdministrativo, blank=True, null=True, verbose_name=_(u'Status'))
    documento = models.ForeignKey(DocumentoAdministrativo)
    data_tramitacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Local'))
    data_encaminhamento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Destino'))
    ultima = models.BooleanField()
    texto = models.TextField(blank=True, null=True, verbose_name=_(u'Texto da Ação'))
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim do Prazo'))

    class Meta:
        verbose_name = _(u'Tramitação de Documento Administrativo')
        verbose_name_plural = _(u'Tramitações de Documento Administrativo')
