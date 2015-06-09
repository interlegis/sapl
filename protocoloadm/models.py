from django.db import models

from materia.models import Autor, TipoMateriaLegislativa


class TipoDocumentoAdministrativo(models.Model):
    sgl_tipo_documento = models.CharField(max_length=5)
    des_tipo_documento = models.CharField(max_length=50)


class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(TipoDocumentoAdministrativo)
    num_documento = models.IntegerField()
    ano_documento = models.SmallIntegerField()
    data_documento = models.DateField()
    num_protocolo = models.IntegerField(blank=True, null=True)
    txt_interessado = models.CharField(max_length=50, blank=True, null=True)
    autor = models.ForeignKey(Autor, blank=True, null=True)
    num_dias_prazo = models.IntegerField(blank=True, null=True)
    data_fim_prazo = models.DateField(blank=True, null=True)
    ind_tramitacao = models.IntegerField()
    txt_assunto = models.TextField()
    txt_observacao = models.TextField(blank=True, null=True)


class DocumentoAcessorioAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo)
    tipo = models.ForeignKey(TipoDocumentoAdministrativo)
    nome_documento = models.CharField(max_length=30)
    nome_arquivo = models.CharField(max_length=100)
    data_documento = models.DateField(blank=True, null=True)
    nome_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_assunto = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)


class Protocolo(models.Model):
    num_protocolo = models.IntegerField(blank=True, null=True)
    ano_protocolo = models.SmallIntegerField()
    data_protocolo = models.DateField()
    hora_protocolo = models.TimeField()
    data_timestamp = models.DateTimeField()
    tipo_protocolo = models.IntegerField()
    tipo_processo = models.IntegerField()
    txt_interessado = models.CharField(max_length=60, blank=True, null=True)
    autor = models.ForeignKey(Autor, blank=True, null=True)
    txt_assunto_ementa = models.TextField(blank=True, null=True)
    tipo_documento = models.ForeignKey(TipoDocumentoAdministrativo, blank=True, null=True)
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True)
    num_paginas = models.IntegerField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_anulado = models.IntegerField()
    txt_user_anulacao = models.CharField(max_length=20, blank=True, null=True)
    txt_ip_anulacao = models.CharField(max_length=15, blank=True, null=True)
    txt_just_anulacao = models.CharField(max_length=60, blank=True, null=True)
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)


class StatusTramitacaoAdministrativo(models.Model):
    sgl_status = models.CharField(max_length=10)
    des_status = models.CharField(max_length=60)
    ind_fim_tramitacao = models.IntegerField()
    ind_retorno_tramitacao = models.IntegerField()


class TramitacaoAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo)
    data_tramitacao = models.DateField(blank=True, null=True)
    cod_unid_tram_local = models.IntegerField(blank=True, null=True)
    data_encaminha = models.DateField(blank=True, null=True)
    cod_unid_tram_dest = models.IntegerField(blank=True, null=True)
    status = models.ForeignKey(StatusTramitacaoAdministrativo, blank=True, null=True)
    ind_ult_tramitacao = models.IntegerField()
    txt_tramitacao = models.TextField(blank=True, null=True)
    data_fim_prazo = models.DateField(blank=True, null=True)
