from django.db import models

from materia.models import Autor, TipoMateriaLegislativa


class TipoDocumentoAdministrativo(models.Model):
    sigla_tipo_documento = models.CharField(max_length=5)       # sgl_tipo_documento
    descricao_tipo_documento = models.CharField(max_length=50)  # des_tipo_documento


class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(TipoDocumentoAdministrativo)                     # tip_documento
    numero_documento = models.IntegerField()                                  # num_documento
    ano_documento = models.SmallIntegerField()                                # ano_documento
    data_documento = models.DateField()                                       # dat_documento
    numero_protocolo = models.IntegerField(blank=True, null=True)             # num_protocolo
    txt_interessado = models.CharField(max_length=50, blank=True, null=True)  # txt_interessado
    autor = models.ForeignKey(Autor, blank=True, null=True)                   # cod_autor
    numero_dias_prazo = models.IntegerField(blank=True, null=True)            # num_dias_prazo
    data_fim_prazo = models.DateField(blank=True, null=True)                  # dat_fim_prazo
    tramitacao = models.BooleanField()                                        # ind_tramitacao
    txt_assunto = models.TextField()                                          # txt_assunto
    txt_observacao = models.TextField(blank=True, null=True)                  # txt_observacao


class DocumentoAcessorioAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo)                         # cod_documento
    tipo = models.ForeignKey(TipoDocumentoAdministrativo)                          # tip_documento
    nome_documento = models.CharField(max_length=30)                               # nom_documento
    nome_arquivo = models.CharField(max_length=100)                                # nom_arquivo
    data_documento = models.DateField(blank=True, null=True)                       # dat_documento
    nome_autor_documento = models.CharField(max_length=50, blank=True, null=True)  # nom_autor_documento
    txt_assunto = models.TextField(blank=True, null=True)                          # txt_assunto
    txt_indexacao = models.TextField(blank=True, null=True)                        # txt_indexacao


class Protocolo(models.Model):
    numero_protocolo = models.IntegerField(blank=True, null=True)                           # num_protocolo
    ano_protocolo = models.SmallIntegerField()                                              # ano_protocolo
    data_protocolo = models.DateField()                                                     # dat_protocolo
    hora_protocolo = models.TimeField()                                                     # hor_protocolo
    data_timestamp = models.DateTimeField()                                                 # dat_timestamp
    tipo_protocolo = models.IntegerField()                                                  # tip_protocolo
    tipo_processo = models.IntegerField()                                                   # tip_processo
    txt_interessado = models.CharField(max_length=60, blank=True, null=True)                # txt_interessado
    autor = models.ForeignKey(Autor, blank=True, null=True)                                 # cod_autor
    txt_assunto_ementa = models.TextField(blank=True, null=True)                            # txt_assunto_ementa
    tipo_documento = models.ForeignKey(TipoDocumentoAdministrativo, blank=True, null=True)  # tip_documento
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True)         # tip_materia
    numero_paginas = models.IntegerField(blank=True, null=True)                             # num_paginas
    txt_observacao = models.TextField(blank=True, null=True)                                # txt_observacao
    anulado = models.BooleanField()                                                         # ind_anulado
    txt_user_anulacao = models.CharField(max_length=20, blank=True, null=True)              # txt_user_anulacao
    txt_ip_anulacao = models.CharField(max_length=15, blank=True, null=True)                # txt_ip_anulacao
    txt_just_anulacao = models.CharField(max_length=60, blank=True, null=True)              # txt_just_anulacao
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)                        # timestamp_anulacao


class StatusTramitacaoAdministrativo(models.Model):
    sigla_status = models.CharField(max_length=10)      # sgl_status
    descricao_status = models.CharField(max_length=60)  # des_status
    fim_tramitacao = models.BooleanField()              # ind_fim_tramitacao
    retorno_tramitacao = models.BooleanField()          # ind_retorno_tramitacao


class TramitacaoAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo)                             # cod_documento
    data_tramitacao = models.DateField(blank=True, null=True)                          # dat_tramitacao
    cod_unid_tram_local = models.IntegerField(blank=True, null=True)                   # cod_unid_tram_local
    data_encaminha = models.DateField(blank=True, null=True)                           # dat_encaminha
    cod_unid_tram_dest = models.IntegerField(blank=True, null=True)                    # cod_unid_tram_dest
    status = models.ForeignKey(StatusTramitacaoAdministrativo, blank=True, null=True)  # cod_status
    ult_tramitacao = models.BooleanField()                                             # ind_ult_tramitacao
    txt_tramitacao = models.TextField(blank=True, null=True)                           # txt_tramitacao
    data_fim_prazo = models.DateField(blank=True, null=True)                           # dat_fim_prazo
