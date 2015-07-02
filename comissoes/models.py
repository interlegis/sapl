# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from parlamentares.models import Parlamentar


class TipoComissao(models.Model):
    TEMPORARY = 'T'
    PERMANENT = 'P'
    NATURE_CHOICES = ((TEMPORARY, _(u'Temporária')),
                      (PERMANENT, _(u'Permanente')))
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))                                                             # nom_tipo_comissao
    natureza_comissao = models.CharField(max_length=1, verbose_name=_(u'Natureza'), choices=NATURE_CHOICES, default=PERMANENT)  # sgl_natureza_comissao
    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))                                                           # sgl_tipo_comissao
    dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Dispositivo Regimental'))  # des_dispositivo_regimental

    class Meta:
        verbose_name = _(u'Tipo de Comissão')
        verbose_name_plural = _(u'Tipos de Comissão')

    def __unicode__(self):
        return self.nome


class Comissao(models.Model):
    tipo = models.ForeignKey(TipoComissao, verbose_name=_(u'Tipo'))                                                  # tip_comissao
    nome = models.CharField(max_length=60, verbose_name=_(u'Nome'))                                      # nom_comissao
    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))                                                # sgl_comissao
    data_criacao = models.DateField(verbose_name=_(u'Data de Criação'))                                                          # dat_criacao
    data_extincao = models.DateField(blank=True, null=True, verbose_name=_(u'Data de Extinção'))                                 # dat_extincao
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
    finalidade = models.TextField(blank=True, null=True, verbose_name=_(u'Finalidade'))                                   # txt_finalidade
    email = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'E-mail'))                                # end_email
    unid_deliberativa = models.BooleanField()                                                                                 # ind_unid_deliberativa

    class Meta:
        verbose_name = _(u'Comissão')
        verbose_name_plural = _(u'Comissões')

    def __unicode__(self):
        return self.nome


class Periodo(models.Model):  # PeriodoCompComissao
    data_inicio = models.DateField(verbose_name=_(u'Data Início'))                   # dat_inicio_periodo
    data_fim = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim'))  # dat_fim_periodo

    class Meta:
        verbose_name = _(u'Período de composição de Comissão')
        verbose_name_plural = _(u'Períodos de composição de Comissão')

    def __unicode__(self):
        return '%s - %s' % (self.data_inicio, self.data_fim)


class CargoComissao(models.Model):
    nome = models.CharField(max_length=50, verbose_name=_(u'Cargo'))  # des_cargo
    unico = models.BooleanField(verbose_name=_(u'Único'))             # ind_unico

    class Meta:
        verbose_name = _(u'Cargo de Comissão')
        verbose_name_plural = _(u'Cargos de Comissão')

    def __unicode__(self):
        return self.nome


class Composicao(models.Model):  # IGNORE
    comissao = models.ForeignKey(Comissao, verbose_name=_(u'Comissão'))  # cod_comissao
    periodo = models.ForeignKey(Periodo, verbose_name=_(u'Período'))    # cod_periodo_comp

    class Meta:
        verbose_name = _(u'Composição de Comissão')
        verbose_name_plural = _(u'Composições de Comissão')


class Participacao(models.Model):  # ComposicaoComissao
    composicao = models.ForeignKey(Composicao)                                                                             # cod_comissao
    parlamentar = models.ForeignKey(Parlamentar)                                                                           # cod_parlamentar
    cargo = models.ForeignKey(CargoComissao)                                                                               # cod_cargo
    titular = models.BooleanField(verbose_name=_(u'Titular'))                                                              # ind_titular
    data_designacao = models.DateField(verbose_name=_(u'Data Designação'))                                                 # dat_designacao
    data_desligamento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desligamento'))                      # dat_desligamento
    motivo_desligamento = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Motivo Desligamento'))  # des_motivo_desligamento
    observacao = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Observação'))                    # obs_composicao

    class Meta:
        verbose_name = _(u'Participação em Comissão')
        verbose_name_plural = _(u'Participações em Comissão')

    def __unicode__(self):
        return 'TODO...'

