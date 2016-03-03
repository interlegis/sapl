"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from parlamentares.models import Parlamentar
from sapl.utils import YES_NO_CHOICES


class TipoComissao(models.Model):
    NATUREZA_CHOICES = Choices(('T', 'temporaria', _('Temporária')),
                               ('P', 'permanente', _('Permanente')))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    natureza = models.CharField(
        max_length=1, verbose_name=_('Natureza'), choices=NATUREZA_CHOICES)
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    dispositivo_regimental = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Dispositivo Regimental'))

    class Meta:
        verbose_name = _('Tipo de Comissão')
        verbose_name_plural = _('Tipos de Comissão')

    def __str__(self):
        return self.nome


class Comissao(models.Model):
    tipo = models.ForeignKey(TipoComissao, verbose_name=_('Tipo'))
    nome = models.CharField(max_length=60, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    data_criacao = models.DateField(verbose_name=_('Data de Criação'))
    data_extincao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Extinção'))
    apelido_temp = models.CharField(
        max_length=100, blank=True, verbose_name=_('Apelido'))
    data_instalacao_temp = models.DateField(
        blank=True, null=True, verbose_name=_('Data Instalação'))
    data_final_prevista_temp = models.DateField(
        blank=True, null=True, verbose_name=_('Data Prevista Término'))
    data_prorrogada_temp = models.DateField(
        blank=True, null=True, verbose_name=_('Novo Prazo'))
    data_fim_comissao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Término'))
    secretario = models.CharField(
        max_length=30, blank=True, verbose_name=_('Secretário'))
    telefone_reuniao = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Tel. Sala Reunião'))
    endereco_secretaria = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Endereço Secretaria'))
    telefone_secretaria = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Tel. Secretaria'))
    fax_secretaria = models.CharField(
        max_length=15, blank=True, verbose_name=_('Fax Secretaria'))
    agenda_reuniao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Data/Hora Reunião'))
    local_reuniao = models.CharField(
        max_length=100, blank=True, verbose_name=_('Local Reunião'))
    finalidade = models.TextField(
        blank=True, verbose_name=_('Finalidade'))
    email = models.CharField(
        max_length=100, blank=True, verbose_name=_('E-mail'))
    unidade_deliberativa = models.BooleanField(
        choices=YES_NO_CHOICES,
        verbose_name=_('Unidade Deliberativa'))

    class Meta:
        verbose_name = _('Comissão')
        verbose_name_plural = _('Comissões')

    def __str__(self):
        return self.nome


class Periodo(models.Model):  # PeriodoCompComissao
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim'))

    class Meta:
        verbose_name = _('Período de composição de Comissão')
        verbose_name_plural = _('Períodos de composição de Comissão')

    def __str__(self):
        return '%s - %s' % (self.data_inicio, self.data_fim)


class CargoComissao(models.Model):
    nome = models.CharField(max_length=50, verbose_name=_('Cargo'))
    unico = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Único'))

    class Meta:
        verbose_name = _('Cargo de Comissão')
        verbose_name_plural = _('Cargos de Comissão')

    def __str__(self):
        return self.nome


class Composicao(models.Model):  # IGNORE
    comissao = models.ForeignKey(Comissao, verbose_name=_('Comissão'))
    periodo = models.ForeignKey(Periodo, verbose_name=_('Período'))

    class Meta:
        verbose_name = _('Composição de Comissão')
        verbose_name_plural = _('Composições de Comissão')

    def __str__(self):
        return '%s: %s' % (self.comissao.sigla, self.periodo)


class Participacao(models.Model):  # ComposicaoComissao
    composicao = models.ForeignKey(Composicao)
    parlamentar = models.ForeignKey(Parlamentar)
    cargo = models.ForeignKey(CargoComissao)
    titular = models.BooleanField(verbose_name=_('Titular'))
    data_designacao = models.DateField(verbose_name=_('Data Designação'))
    data_desligamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desligamento'))
    motivo_desligamento = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Motivo Desligamento'))
    observacao = models.CharField(
        max_length=150, blank=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Participação em Comissão')
        verbose_name_plural = _('Participações em Comissão')

    def __str__(self):
        return '%s : %s' % (self.cargo, self.parlamentar)
