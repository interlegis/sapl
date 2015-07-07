# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from materia.models import MateriaLegislativa
from parlamentares.models import CargoMesa, Parlamentar, SessaoLegislativa, Legislatura
from sapl.utils import make_choices


class TipoSessaoPlenaria(models.Model):
    nome = models.CharField(max_length=30, verbose_name=_(u'Tipo'))
    quorum_minimo = models.IntegerField(verbose_name=_(u'Quórum mínimo'))

    class Meta:
        verbose_name = _(u'Tipo de Sessão Plenária')
        verbose_name_plural = _(u'Tipos de Sessão Plenária')

    def __unicode__(self):
        return self.nome


class SessaoPlenaria(models.Model):
    # TODO trash??? Seems to have been a FK in the past. Would be:
    # andamento_sessao = models.ForeignKey(AndamentoSessao, blank=True, null=True)
    # TODO analyze querying all hosted databases !
    cod_andamento_sessao = models.IntegerField(blank=True, null=True)

    tipo = models.ForeignKey(TipoSessaoPlenaria, verbose_name=_(u'Tipo'))
    sessao_legislativa = models.ForeignKey(SessaoLegislativa, verbose_name=_(u'Sessão Legislativa'))
    legislatura = models.ForeignKey(Legislatura, verbose_name=_(u'Legislatura'))
    # XXX seems to be empty
    tipo_expediente = models.CharField(max_length=10)
    data_inicio = models.DateField(verbose_name=_(u'Abertura'))
    dia = models.CharField(max_length=15)
    hora_inicio = models.CharField(max_length=5, verbose_name=_(u'Horário'))
    hora_fim = models.CharField(max_length=5, blank=True, null=True, verbose_name=_(u'Horário'))
    numero = models.IntegerField(verbose_name=_(u'Número'))
    data_fim = models.DateField(blank=True, null=True, verbose_name=_(u'Encerramento'))
    url_audio = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'URL Arquivo Áudio (Formatos MP3 / AAC)'))
    url_video = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))

    class Meta:
        verbose_name = _(u'Sessão Plenária')
        verbose_name_plural = _(u'Sessões Plenárias')

    def __unicode__(self):
        return _(u'%sª Sessão %s da %sª Sessão Legislativa da %sª Legislatura') % (
            self.numero,
            self.tipo.nome,
            self.sessao_legislativa.numero,
            self.legislatura.id)  # XXX check if it shouldn't be legislatura.numero


class AbstractOrdemDia(models.Model):
    TIPO_VOTACAO_CHOICES, SIMBOLICA, NOMINAL, SECRETA = make_choices(
        1, _(u'Simbólica'),
        2, _(u'Nominal'),
        3, _(u'Secreta'),
    )

    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    materia = models.ForeignKey(MateriaLegislativa)
    data_ordem = models.DateField(verbose_name=_(u'Data da Sessão'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Ementa'))
    numero_ordem = models.IntegerField(verbose_name=_(u'Nº Ordem'))
    resultado = models.TextField(blank=True, null=True)
    tipo_votacao = models.IntegerField(verbose_name=_(u'Tipo de votação'), choices=TIPO_VOTACAO_CHOICES)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s - %s' % (self.numero_ordem, self.sessao_plenaria)


class ExpedienteMateria(AbstractOrdemDia):

    class Meta:
        verbose_name = _(u'Matéria do Expediente')
        verbose_name_plural = _(u'Matérias do Expediente')


class TipoExpediente(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_(u'Tipo'))

    class Meta:
        verbose_name = _(u'Tipo de Expediente')
        verbose_name_plural = _(u'Tipos de Expediente')

    def __unicode__(self):
        return self.nome


class ExpedienteSessao(models.Model):  # ExpedienteSessaoPlenaria
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    tipo = models.ForeignKey(TipoExpediente)
    conteudo = models.TextField(blank=True, null=True, verbose_name=_(u'Conteúdo do expediente'))

    class Meta:
        verbose_name = _(u'Expediente de Sessão Plenaria')
        verbose_name_plural = _(u'Expedientes de Sessão Plenaria')

    def __unicode__(self):
        return u'%s - %s' % (self.tipo, self.sessao_plenaria)


class IntegranteMesa(models.Model):  # MesaSessaoPlenaria
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    cargo = models.ForeignKey(CargoMesa)
    parlamentar = models.ForeignKey(Parlamentar)

    class Meta:
        verbose_name = _(u'Participação em Mesa de Sessão Plenaria')
        verbose_name_plural = _(u'Participações em Mesas de Sessão Plenaria')

    def __unicode__(self):
        return u'%s - %s' % (self.cargo, self.parlamentar)


class AbstractOrador(models.Model):  # Oradores
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar, verbose_name=_(u'Parlamentar'))
    numero_ordem = models.IntegerField(verbose_name=_(u'Ordem de pronunciamento'))
    url_discurso = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'URL Vídeo'))

    class Meta:
        abstract = True

    def __unicode__(self):
        return _(u'%(nome)s (%(numero)sº orador)') % {
            'nome': self.parlamentar,
            'numero': self.numero_ordem}


class Orador(AbstractOrador):  # Oradores

    class Meta:
        verbose_name = _(u'Orador das Explicações Pessoais')
        verbose_name_plural = _(u'Oradores das Explicações Pessoais')


class OradorExpediente(AbstractOrador):  # OradoresExpediente

    class Meta:
        verbose_name = _(u'Orador do Expediente')
        verbose_name_plural = _(u'Oradores do Expediente')


class OrdemDia(AbstractOrdemDia):

    class Meta:
        verbose_name = _(u'Matéria da Ordem do Dia')
        verbose_name_plural = _(u'Matérias da Ordem do Dia')


class PresencaOrdemDia(models.Model):  # OrdemDiaPresenca
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    data_ordem = models.DateField()

    class Meta:
        verbose_name = _(u'Presença da Ordem do Dia')
        verbose_name_plural = _(u'Presenças da Ordem do Dia')

    def __unicode__(self):
        return self.parlamentar


class TipoResultadoVotacao(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_(u'Tipo'))

    class Meta:
        verbose_name = _(u'Tipo de Resultado de Votação')
        verbose_name_plural = _(u'Tipos de Resultado de Votação')

    def __unicode__(self):
        return self.nome


class RegistroVotacao(models.Model):
    tipo_resultado_votacao = models.ForeignKey(TipoResultadoVotacao, verbose_name=_(u'Resultado da Votação'))
    materia = models.ForeignKey(MateriaLegislativa)
    ordem = models.ForeignKey(OrdemDia)
    numero_votos_sim = models.IntegerField(verbose_name=_(u'Sim'))
    numero_votos_nao = models.IntegerField(verbose_name=_(u'Não'))
    numero_abstencoes = models.IntegerField(verbose_name=_(u'Abstenções'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observações'))

    class Meta:
        verbose_name = _(u'Votação')
        verbose_name_plural = _(u'Votações')

    def __unicode__(self):
        return self.materia  # XXX ?


class VotoParlamentar(models.Model):  # RegistroVotacaoParlamentar
    votacao = models.ForeignKey(RegistroVotacao)
    parlamentar = models.ForeignKey(Parlamentar)
    # XXX change to restricted choices
    voto = models.CharField(max_length=10)

    class Meta:
        verbose_name = _(u'Registro de Votação de Parlamentar')
        verbose_name_plural = _(u'Registros de Votações de Parlamentares')

    def __unicode__(self):
        return self.parlamentar  # XXX ?


class SessaoPlenariaPresenca(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    data_sessao = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = _(u'Presença em Sessão Plenária')
        verbose_name_plural = _(u'Presenças em Sessões Plenárias')

    def __unicode__(self):
        return self.parlamentar  # XXX ?
