# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from parlamentares.models import Parlamentar


class TipoComissao(models.Model):
    TEMPORARIA = 'T'
    PERMANENTE = 'P'
    NATUREZA_CHOICES = ((TEMPORARIA, _(u'Temporária')),
                        (PERMANENTE, _(u'Permanente')))
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))
    natureza = models.CharField(max_length=1, verbose_name=_(u'Natureza'), choices=NATUREZA_CHOICES)
    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))
    dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Dispositivo Regimental'))

    class Meta:
        verbose_name = _(u'Tipo de Comissão')
        verbose_name_plural = _(u'Tipos de Comissão')

    def __unicode__(self):
        return self.nome


class Comissao(models.Model):
    tipo = models.ForeignKey(TipoComissao, verbose_name=_(u'Tipo'))
    nome = models.CharField(max_length=60, verbose_name=_(u'Nome'))
    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))
    data_criacao = models.DateField(verbose_name=_(u'Data de Criação'))
    data_extincao = models.DateField(blank=True, null=True, verbose_name=_(u'Data de Extinção'))
    apelido_temp = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Apelido'))
    data_instalacao_temp = models.DateField(blank=True, null=True, verbose_name=_(u'Data Instalação'))
    data_final_prevista_temp = models.DateField(blank=True, null=True, verbose_name=_(u'Data Prevista Término'))
    data_prorrogada_temp = models.DateField(blank=True, null=True, verbose_name=_(u'Novo Prazo'))
    data_fim_comissao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Término'))
    secretario = models.CharField(max_length=30, blank=True, null=True, verbose_name=_(u'Secretário'))
    telefone_reuniao = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Tel. Sala Reunião'))
    endereco_secretaria = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Endereço Secretaria'))
    telefone_secretaria = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Tel. Secretaria'))
    fax_secretaria = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Fax Secretaria'))
    agenda_reuniao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Data/Hora Reunião'))
    local_reuniao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Local Reunião'))
    finalidade = models.TextField(blank=True, null=True, verbose_name=_(u'Finalidade'))
    email = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'E-mail'))
    unidade_deliberativa = models.BooleanField()

    class Meta:
        verbose_name = _(u'Comissão')
        verbose_name_plural = _(u'Comissões')

    def __unicode__(self):
        return self.nome


class Periodo(models.Model):  # PeriodoCompComissao
    data_inicio = models.DateField(verbose_name=_(u'Data Início'))
    data_fim = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim'))

    class Meta:
        verbose_name = _(u'Período de composição de Comissão')
        verbose_name_plural = _(u'Períodos de composição de Comissão')

    def __unicode__(self):
        return '%s - %s' % (self.data_inicio, self.data_fim)


class CargoComissao(models.Model):
    nome = models.CharField(max_length=50, verbose_name=_(u'Cargo'))
    unico = models.BooleanField(verbose_name=_(u'Único'))

    class Meta:
        verbose_name = _(u'Cargo de Comissão')
        verbose_name_plural = _(u'Cargos de Comissão')

    def __unicode__(self):
        return self.nome


class Composicao(models.Model):  # IGNORE
    comissao = models.ForeignKey(Comissao, verbose_name=_(u'Comissão'))
    periodo = models.ForeignKey(Periodo, verbose_name=_(u'Período'))

    class Meta:
        verbose_name = _(u'Composição de Comissão')
        verbose_name_plural = _(u'Composições de Comissão')

    def __unicode__(self):
        return '%s: %s' % (self.comissao.sigla, self.periodo)


class Participacao(models.Model):  # ComposicaoComissao
    composicao = models.ForeignKey(Composicao)
    parlamentar = models.ForeignKey(Parlamentar)
    cargo = models.ForeignKey(CargoComissao)
    titular = models.BooleanField(verbose_name=_(u'Titular'))
    data_designacao = models.DateField(verbose_name=_(u'Data Designação'))
    data_desligamento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desligamento'))
    motivo_desligamento = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Motivo Desligamento'))
    observacao = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Observação'))

    class Meta:
        verbose_name = _(u'Participação em Comissão')
        verbose_name_plural = _(u'Participações em Comissão')

    def __unicode__(self):
        return '%s : %s' % (self.cargo, self.parlamentar)

