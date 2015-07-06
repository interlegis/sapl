# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from materia.models import MateriaLegislativa
from parlamentares.models import CargoMesa, Parlamentar, SessaoLegislativa, Legislatura
from sapl.utils import make_choices


class TipoSessaoPlenaria(models.Model):
    nome = models.CharField(max_length=30, verbose_name=_(u'Tipo'))  # nom_sessao
    quorum_minimo = models.IntegerField(verbose_name=_(u'Quórum mínimo'))   # num_minimo

    class Meta:
        verbose_name = _(u'Tipo de Sessão Plenária')
        verbose_name_plural = _(u'Tipos de Sessão Plenária')

    def __unicode__(self):
        return self.nome_sessao

class SessaoPlenaria(models.Model):
    # TODO trash??? Seems to have been a FK in the past. Would be:
    # andamento_sessao = models.ForeignKey(AndamentoSessao, blank=True, null=True)
    # TODO analyze querying all hosted databases !
    cod_andamento_sessao = models.IntegerField(blank=True, null=True)                                                                      # cod_andamento_sessao

    tipo = models.ForeignKey(TipoSessaoPlenaria, verbose_name=_(u'Tipo'))                                                                                           # tip_sessao
    sessao_legislativa = models.ForeignKey(SessaoLegislativa, verbose_name=_(u'Sessão Legislativa'))                                                                                      # cod_sessao_leg
    legislatura = models.ForeignKey(Legislatura, verbose_name=_(u'Legislatura'))                                                           # num_legislatura
    # XXX seems to be empty
    tipo_expediente = models.CharField(max_length=10)                                                                                      # tip_expediente
    data_inicio = models.DateField(verbose_name=_(u'Abertura'))                                                                     # dat_inicio_sessao
    dia = models.CharField(max_length=15)                                                                                           # dia_sessao
    hora_inicio = models.CharField(max_length=5, verbose_name=_(u'Horário'))                                                                                      # hr_inicio_sessao
    hora_fim = models.CharField(max_length=5, blank=True, null=True, verbose_name=_(u'Horário'))                                                                  # hr_fim_sessao
    numero = models.IntegerField(verbose_name=_(u'Número'))                                                                    # num_sessao_plen
    data_fim = models.DateField(blank=True, null=True, verbose_name=_(u'Encerramento'))                                             # dat_fim_sessao
    url_audio = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'URL Arquivo Áudio (Formatos MP3 / AAC)'))         # url_audio
    url_video = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))  # url_video

    class Meta:
        verbose_name = _(u'Sessão Plenária')
        verbose_name_plural = _(u'Sessões Plenárias')

    def __unicode__(self):
        return u'%s - %s - %s' % (self.numero_sessao_plen, self.sessao_plen, self.legislatura)

class AbstractOrdemDia(models.Model):
    TIPO_VOTACAO_CHOICES, SIMBOLICA, NOMINAL, SECRETA = make_choices(
        1, _(u'Simbólica'),
        2, _(u'Nominal'),
        3, _(u'Secreta'),
    )

    sessao_plenaria = models.ForeignKey(SessaoPlenaria)                                      # cod_sessao_plen
    materia = models.ForeignKey(MateriaLegislativa)                                      # cod_materia
    data_ordem = models.DateField(verbose_name=_(u'Data da Sessão'))                     # dat_ordem
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Ementa'))  # txt_observacao
    numero_ordem = models.IntegerField(verbose_name=_(u'Nº Ordem'))                      # num_ordem
    resultado = models.TextField(blank=True, null=True)                              # txt_resultado
    tipo_votacao = models.IntegerField(verbose_name=_(u'Tipo de votação'), choices=TIPO_VOTACAO_CHOICES)  # tip_votacao

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s - %s' % (self.numero_ordem, self.sessao_plen)


class ExpedienteMateria(AbstractOrdemDia):

    class Meta:
        verbose_name = _(u'Matéria do Expediente')
        verbose_name_plural = _(u'Matérias do Expediente')


class TipoExpediente(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_(u'Tipo'))  # nom_expediente

    class Meta:
        verbose_name = _(u'Tipo de Expediente')
        verbose_name_plural = _(u'Tipos de Expediente')

    def __unicode__(self):
        return self.nome

class ExpedienteSessao(models.Model):  # ExpedienteSessaoPlenaria
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)           # cod_sessao_plen
    tipo = models.ForeignKey(TipoExpediente)            # cod_expediente
    conteudo = models.TextField(blank=True, null=True, verbose_name=_(u'Conteúdo do expediente'))  # txt_expediente

    class Meta:
        verbose_name = _(u'Expediente de Sessão Plenaria')
        verbose_name_plural = _(u'Expedientes de Sessão Plenaria')

    def __unicode__(self):
        return u'%s - %s' % (self.cod_expediente, self.sessao_plen)

class IntegranteMesa(models.Model):  # MesaSessaoPlenaria
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)    # cod_sessao_plen
    cargo = models.ForeignKey(CargoMesa)               # cod_cargo
    parlamentar = models.ForeignKey(Parlamentar)       # cod_parlamentar

    class Meta:
        verbose_name = _(u'Participação em Mesa de Sessão Plenaria')
        verbose_name_plural = _(u'Participações em Mesas de Sessão Plenaria')

    def __unicode__(self):
        return self.parlamentar

class AbstractOrador(models.Model):  # Oradores
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)                                                       # cod_sessao_plen
    parlamentar = models.ForeignKey(Parlamentar, verbose_name=_(u'Parlamentar'))                          # cod_parlamentar
    numero_ordem = models.IntegerField(verbose_name=_(u'Ordem de pronunciamento'))                        # num_ordem
    url_discurso = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'URL Vídeo'))  # url_discurso

    class Meta:
        abstract = True


class Orador(AbstractOrador):  # Oradores

    class Meta:
        verbose_name = _(u'Orador das Explicações Pessoais')
        verbose_name_plural = _(u'Oradores das Explicações Pessoais')

    def __unicode__(self):
        return self.parlamentar

class OradorExpediente(AbstractOrador):  # OradoresExpediente

    class Meta:
        verbose_name = _(u'Orador do Expediente')
        verbose_name_plural = _(u'Oradores do Expediente')

    def __unicode__(self):
        return self.parlamentar

class OrdemDia(AbstractOrdemDia):

    class Meta:
        verbose_name = _(u'Matéria da Ordem do Dia')
        verbose_name_plural = _(u'Matérias da Ordem do Dia')

    def __unicode__(self):
        return self.numero_ordem

class PresencaOrdemDia(models.Model):  # OrdemDiaPresenca
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)  # cod_sessao_plen
    parlamentar = models.ForeignKey(Parlamentar)     # cod_parlamentar
    data_ordem = models.DateField()                  # dat_ordem

    class Meta:
        verbose_name = _(u'Presença da Ordem do Dia')
        verbose_name_plural = _(u'Presenças da Ordem do Dia')

    def __unicode__(self):
        return self.parlamentar

class TipoResultadoVotacao(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_(u'Tipo'))  # nom_resultado

    class Meta:
        verbose_name = _(u'Tipo de Resultado de Votação')
        verbose_name_plural = _(u'Tipos de Resultado de Votação')

    def __unicode__(self):
        return self.nome_resultado

class RegistroVotacao(models.Model):
    tipo_resultado_votacao = models.ForeignKey(TipoResultadoVotacao, verbose_name=_(u'Resultado da Votação'))  # tip_resultado_votacao
    materia = models.ForeignKey(MateriaLegislativa)                                                            # cod_materia
    ordem = models.ForeignKey(OrdemDia)                                                                        # cod_ordem
    numero_votos_sim = models.IntegerField(verbose_name=_(u'Sim'))                                            # num_votos_sim
    numero_votos_nao = models.IntegerField(verbose_name=_(u'Não'))                                            # num_votos_nao
    numero_abstencoes = models.IntegerField(verbose_name=_(u'Abstenções'))                                     # num_abstencao
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observações'))                   # txt_observacao

    class Meta:
        verbose_name = _(u'Votação')
        verbose_name_plural = _(u'Votações')

    def __unicode__(self):
        return self.materia

class VotoParlamentar(models.Model):  # RegistroVotacaoParlamentar
    votacao = models.ForeignKey(RegistroVotacao)       # cod_votacao
    parlamentar = models.ForeignKey(Parlamentar)       # cod_parlamentar
    # XXX change to restricted choices
    voto = models.CharField(max_length=10)  # vot_parlamentar

    class Meta:
        verbose_name = _(u'Registro de Votação de Parlamentar')
        verbose_name_plural = _(u'Registros de Votações de Parlamentares')

    def __unicode__(self):
        return self.parlamentar

class SessaoPlenariaPresenca(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)        # cod_sessao_plen
    parlamentar = models.ForeignKey(Parlamentar)           # cod_parlamentar
    data_sessao = models.DateField(blank=True, null=True)  # dat_sessao

    class Meta:
        verbose_name = _(u'Presença em Sessão Plenária')
        verbose_name_plural = _(u'Presenças em Sessões Plenárias')

    def __unicode__(self):
        return self.parlamentar