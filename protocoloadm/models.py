# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from materia.models import Autor, TipoMateriaLegislativa, UnidadeTramitacao


class TipoDocumentoAdministrativo(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_(u'Sigla'))           # sgl_tipo_documento
    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))  # des_tipo_documento

    class Meta:
        verbose_name = _(u'Tipo de Documento Administrativo')
        verbose_name_plural = _(u'Tipos de Documento Administrativo')


class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(TipoDocumentoAdministrativo, verbose_name=_(u'Tipo Documento'))                  # tip_documento
    numero = models.IntegerField(verbose_name=_(u'Número'))                                         # num_documento
    ano = models.SmallIntegerField(verbose_name=_(u'Ano'))                                          # ano_documento
    data = models.DateField(verbose_name=_(u'Data'))                                                # dat_documento
    numero_protocolo = models.IntegerField(blank=True, null=True, verbose_name=_(u'Núm. Protocolo'))          # num_protocolo
    interessado = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Interessado'))  # txt_interessado
    autor = models.ForeignKey(Autor, blank=True, null=True)                                                   # cod_autor
    dias_prazo = models.IntegerField(blank=True, null=True, verbose_name=_(u'Dias Prazo'))             # num_dias_prazo
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim Prazo'))               # dat_fim_prazo
    tramitacao = models.BooleanField(verbose_name=_(u'Em Tramitação?'))                                       # ind_tramitacao
    assunto = models.TextField(verbose_name=_(u'Assunto'))                                                # txt_assunto
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))                   # txt_observacao

    class Meta:
        verbose_name = _(u'Documento Administrativo')
        verbose_name_plural = _(u'Documentos Administrativos')


class DocumentoAcessorioAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo)                                                   # cod_documento
    tipo = models.ForeignKey(TipoDocumentoAdministrativo, verbose_name=_(u'Tipo'))                           # tip_documento
    nome = models.CharField(max_length=30, verbose_name=_(u'Nome'))                                # nom_documento
    arquivo = models.CharField(max_length=100, verbose_name=_(u'Arquivo'))                              # nom_arquivo
    data = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))                        # dat_documento
    autor = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Autor'))  # nom_autor_documento
    assunto = models.TextField(blank=True, null=True, verbose_name=_(u'Assunto'))                        # txt_assunto
    indexacao = models.TextField(blank=True, null=True)                                                  # txt_indexacao

    class Meta:
        verbose_name = _(u'Documento Acessório')
        verbose_name_plural = _(u'Documentos Acessórios')


class Protocolo(models.Model):
    numero = models.IntegerField(blank=True, null=True, verbose_name=_(u'Número do Protocolo'))                              # num_protocolo
    ano = models.SmallIntegerField()                                                                                    # ano_protocolo
    data = models.DateField()                                                                                           # dat_protocolo
    hora = models.TimeField()                                                                                           # hor_protocolo
    timestamp = models.DateTimeField()                                                                                       # dat_timestamp
    tipo_protocolo = models.IntegerField(verbose_name=_(u'Tipo de Protocolo'))                                                    # tip_protocolo
    tipo_processo = models.IntegerField()                                                                                         # tip_processo
    interessado = models.CharField(max_length=60, blank=True, null=True, verbose_name=_(u'Interessado'))                      # txt_interessado
    autor = models.ForeignKey(Autor, blank=True, null=True)                                                                       # cod_autor
    assunto_ementa = models.TextField(blank=True, null=True)                                                                  # txt_assunto_ementa
    tipo_documento = models.ForeignKey(TipoDocumentoAdministrativo, blank=True, null=True, verbose_name=_(u'Tipo de documento'))  # tip_documento
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True, verbose_name=_(u'Tipo Matéria'))              # tip_materia
    numero_paginas = models.IntegerField(blank=True, null=True, verbose_name=_(u'Número de Páginas'))                                  # num_paginas
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))                                       # txt_observacao
    anulado = models.BooleanField()                                                                                               # ind_anulado
    user_anulacao = models.CharField(max_length=20, blank=True, null=True)                                                    # txt_user_anulacao
    ip_anulacao = models.CharField(max_length=15, blank=True, null=True)                                                      # txt_ip_anulacao
    justificativa_anulacao = models.CharField(max_length=60, blank=True, null=True)                                                    # txt_just_anulacao
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)                                                              # timestamp_anulacao

    class Meta:
        verbose_name = _(u'Protocolo')
        verbose_name_plural = _(u'Protocolos')


class StatusTramitacaoAdministrativo(models.Model):
    FIM = 'F'
    RETORNO = 'R'
    INDICADOR_CHOICES = ((FIM, _(u'Fim')),
                         (RETORNO, _(u'Retorno')))

    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))          # sgl_status
    descricao = models.CharField(max_length=60, verbose_name=_(u'Descrição'))  # des_status
    # TODO make specific migration considering both ind_fim_tramitacao, ind_retorno_tramitacao
    indicador = models.CharField(max_length=1, verbose_name=_(u'Indicador da Tramitação'), choices=INDICADOR_CHOICES)  # ind_fim_tramitacao

    class Meta:
        verbose_name = _(u'Status de Tramitação')
        verbose_name_plural = _(u'Status de Tramitação')


class TramitacaoAdministrativo(models.Model):
    status = models.ForeignKey(StatusTramitacaoAdministrativo, blank=True, null=True, verbose_name=_(u'Status'))  # cod_status
    documento = models.ForeignKey(DocumentoAdministrativo)                                                        # cod_documento
    data_tramitacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Tramitação'))                                                     # dat_tramitacao
    unidade_tramitacao_local = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Local'))   # cod_unid_tram_local
    data_encaminhamento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Encaminhamento'))                                    # dat_encaminha
    unidade_tramitacao_destino = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Destino'))  # cod_unid_tram_dest
    ultima = models.BooleanField()                                                                                # ind_ult_tramitacao
    texto = models.TextField(blank=True, null=True, verbose_name=_(u'Texto da Ação'))                    # txt_tramitacao
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim do Prazo'))                # dat_fim_prazo

    class Meta:
        verbose_name = _(u'Tramitação de Documento Administrativo')
        verbose_name_plural = _(u'Tramitações de Documento Administrativo')
