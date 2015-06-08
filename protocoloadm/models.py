from django.db import models

from materia.models import Autor, TipoMateriaLegislativa


class TipoDocumentoAdministrativo(models.Model):
    sgl_tipo_documento = models.CharField(max_length=5)
    des_tipo_documento = models.CharField(max_length=50)


class DocumentoAcessorioAdministrativo(models.Model):
    cod_documento_acessorio = models.AutoField(primary_key=True)
    cod_documento = models.IntegerField()
    tipo = models.ForeignKey(TipoDocumentoAdministrativo)
    nom_documento = models.CharField(max_length=30)
    nom_arquivo = models.CharField(max_length=100)
    dat_documento = models.DateField(blank=True, null=True)
    nom_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_assunto = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)


class DocumentoAdministrativo(models.Model):
    cod_documento = models.AutoField(primary_key=True)
    tipo = models.ForeignKey(TipoDocumentoAdministrativo)
    num_documento = models.IntegerField()
    ano_documento = models.SmallIntegerField()
    dat_documento = models.DateField()
    num_protocolo = models.IntegerField(blank=True, null=True)
    txt_interessado = models.CharField(max_length=50, blank=True, null=True)
    autor = models.ForeignKey(Autor, blank=True, null=True)
    num_dias_prazo = models.IntegerField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
    ind_tramitacao = models.IntegerField()
    txt_assunto = models.TextField()
    txt_observacao = models.TextField(blank=True, null=True)


class Protocolo(models.Model):
    cod_protocolo = models.AutoField(primary_key=True)
    num_protocolo = models.IntegerField(blank=True, null=True)
    ano_protocolo = models.SmallIntegerField()
    dat_protocolo = models.DateField()
    hor_protocolo = models.TimeField()
    dat_timestamp = models.DateTimeField()
    tip_protocolo = models.IntegerField()
    tip_processo = models.IntegerField()
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
    cod_documento = models.IntegerField()
    dat_tramitacao = models.DateField(blank=True, null=True)
    cod_unid_tram_local = models.IntegerField(blank=True, null=True)
    dat_encaminha = models.DateField(blank=True, null=True)
    cod_unid_tram_dest = models.IntegerField(blank=True, null=True)
    status = models.ForeignKey(StatusTramitacaoAdministrativo, blank=True, null=True)
    ind_ult_tramitacao = models.IntegerField()
    txt_tramitacao = models.TextField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
