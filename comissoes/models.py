# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from parlamentares.models import Parlamentar


class TipoComissao(models.Model):
    nome_tipo_comissao = models.CharField(max_length=50, verbose_name=_(u'Nome'))                                                         # nom_tipo_comissao
    sigla_natureza_comissao = models.CharField(max_length=1, verbose_name=_(u'Natureza'))                                                 # sgl_natureza_comissao
    sigla_tipo_comissao = models.CharField(max_length=10, verbose_name=_(u'Sigla'))                                                       # sgl_tipo_comissao
    descricao_dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Dispositivo Regimental'))  # des_dispositivo_regimental

    class Meta:
        verbose_name = _(u'Tipo de Comissão')
        verbose_name_plural = _(u'Tipos de Comissão')


class Comissao(models.Model):
    tipo_comissao = models.ForeignKey(TipoComissao, verbose_name=_(u'Tipo'))                                                  # tip_comissao
    nome_comissao = models.CharField(max_length=60, verbose_name=_(u'Nome da Comissâo'))                                      # nom_comissao
    sigla_comissao = models.CharField(max_length=10, verbose_name=_(u'Sigla'))                                                # sgl_comissao
    data_criacao = models.DateField(verbose_name=_(u'Data Criação'))                                                          # dat_criacao
    data_extincao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Extinção'))                                 # dat_extincao
    nome_apelido_temp = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Apelido'))                   # nom_apelido_temp
    data_instalacao_temp = models.DateField(blank=True, null=True, verbose_name=_(u'Data Instalação'))                        # dat_instalacao_temp
    data_final_prevista_temp = models.DateField(blank=True, null=True, verbose_name=_(u'Data Prevista Término'))              # dat_final_prevista_temp
    data_prorrogada_temp = models.DateField(blank=True, null=True, verbose_name=_(u'Novo Prazo'))                             # dat_prorrogada_temp
    data_fim_comissao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Término'))                              # dat_fim_comissao
    nome_secretario = models.CharField(max_length=30, blank=True, null=True, verbose_name=_(u'Secretário'))                   # nom_secretario
    numero_tel_reuniao = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Tel. Sala Reunião'))         # num_tel_reuniao
    endereco_secretaria = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Endereço Secretaria'))     # end_secretaria
    numero_tel_secretaria = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Tel. Secretaria'))        # num_tel_secretaria
    numero_fax_secretaria = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Fax Secretaria'))         # num_fax_secretaria
    descricao_agenda_reuniao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Data/Hora Reunião'))  # des_agenda_reuniao
    local_reuniao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Local Reunião'))                 # loc_reuniao
    txt_finalidade = models.TextField(blank=True, null=True, verbose_name=_(u'Finalidade'))                                   # txt_finalidade
    endereco_email = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'E-mail'))                       # end_email
    unid_deliberativa = models.BooleanField()                                                                                 # ind_unid_deliberativa

    class Meta:
        verbose_name = _(u'Comissão')
        verbose_name_plural = _(u'Comissões')


class PeriodoCompComissao(models.Model):
    data_inicio_periodo = models.DateField(verbose_name=_(u'Data Início'))                   # dat_inicio_periodo
    data_fim_periodo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim'))  # dat_fim_periodo

    class Meta:
        verbose_name = _(u'Período de composição de Comissão')
        verbose_name_plural = _(u'Períodos de composição de Comissão')


class CargoComissao(models.Model):
    nome = models.CharField(max_length=50, verbose_name=_(u'Cargo na Comissão'))  # des_cargo
    unico = models.BooleanField(verbose_name=_(u'Cargo Único'))           # ind_unico

    class Meta:
        verbose_name = _(u'Cargo de Comissão')
        verbose_name_plural = _(u'Cargos de Comissão')


class ComposicaoComissao(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)                                                                                     # cod_parlamentar
    comissao = models.ForeignKey(Comissao)                                                                                           # cod_comissao
    periodo_comp = models.ForeignKey(PeriodoCompComissao)                                                                            # cod_periodo_comp
    cargo = models.ForeignKey(CargoComissao)                                                                                         # cod_cargo
    titular = models.BooleanField(verbose_name=_(u'Titular'))                                                                        # ind_titular
    data_designacao = models.DateField(verbose_name=_(u'Data Designação'))                                                           # dat_designacao
    data_desligamento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desligamento'))                                # dat_desligamento
    descricao_motivo_desligamento = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Motivo Desligamento'))  # des_motivo_desligamento
    obs_composicao = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Observação'))                          # obs_composicao

    class Meta:
        verbose_name = _(u'Composição de Comissão')
        verbose_name_plural = _(u'Composições de Comissão')

