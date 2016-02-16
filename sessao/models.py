from django.db import models
from django.utils.translation import ugettext_lazy as _

from materia.models import MateriaLegislativa
from parlamentares.models import (CargoMesa, Legislatura, Parlamentar,
                                  SessaoLegislativa)
from sapl.utils import YES_NO_CHOICES, make_choices


class TipoSessaoPlenaria(models.Model):
    nome = models.CharField(max_length=30, verbose_name=_('Tipo'))
    quorum_minimo = models.PositiveIntegerField(
        verbose_name=_('Quórum mínimo'))

    class Meta:
        verbose_name = _('Tipo de Sessão Plenária')
        verbose_name_plural = _('Tipos de Sessão Plenária')

    def __str__(self):
        return self.nome


def get_sessao_media_path(instance, subpath, filename):
    return './sessao/%s/%s/%s' % (instance.numero, subpath, filename)


def pauta_upload_path(instance, filename):
    return get_sessao_media_path(instance, 'pauta', filename)


def ata_upload_path(instance, filename):
    return get_sessao_media_path(instance, 'ata', filename)


class SessaoPlenaria(models.Model):
    # TODO trash??? Seems to have been a FK in the past. Would be:
    # andamento_sessao = models.ForeignKey(
    #    AndamentoSessao, blank=True, null=True)
    # TODO analyze querying all hosted databases !
    cod_andamento_sessao = models.PositiveIntegerField(blank=True, null=True)

    tipo = models.ForeignKey(TipoSessaoPlenaria, verbose_name=_('Tipo'))
    sessao_legislativa = models.ForeignKey(
        SessaoLegislativa, verbose_name=_('Sessão Legislativa'))
    legislatura = models.ForeignKey(Legislatura, verbose_name=_('Legislatura'))
    # XXX seems to be empty
    data_inicio = models.DateField(verbose_name=_('Abertura'))
    hora_inicio = models.CharField(
        max_length=5, verbose_name=_('Horário (hh:mm)'))
    hora_fim = models.CharField(
        max_length=5, blank=True, verbose_name=_('Horário (hh:mm)'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    data_fim = models.DateField(
        blank=True, null=True, verbose_name=_('Encerramento'))
    url_audio = models.CharField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Áudio (Formatos MP3 / AAC)'))
    url_video = models.CharField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))
    upload_pauta = models.FileField(
        blank=True,
        null=True,
        upload_to=pauta_upload_path,
        verbose_name=_('Pauta da Sessão'))
    upload_ata = models.FileField(
        blank=True,
        null=True,
        upload_to=ata_upload_path,
        verbose_name=_('Ata da Sessão'))
    iniciada = models.NullBooleanField(blank=True,
                                       choices=YES_NO_CHOICES,
                                       verbose_name=_('Sessão iniciada?'))
    finalizada = models.NullBooleanField(blank=True,
                                         choices=YES_NO_CHOICES,
                                         verbose_name=_('Sessão finalizada?'))

    class Meta:
        verbose_name = _('Sessão Plenária')
        verbose_name_plural = _('Sessões Plenárias')

    def __str__(self):
        return _('%(numero)sª Sessão %(tipo_nome)s'
                 ' da %(sessao_legislativa_numero)sª Sessão Legislativa'
                 ' da %(legislatura_id)sª Legislatura') % {

            'numero': self.numero,
            'tipo_nome': self.tipo.nome,
            'sessao_legislativa_numero': self.sessao_legislativa.numero,
            # XXX check if it shouldn't be legislatura.numero
            'legislatura_id': self.legislatura.id}


class AbstractOrdemDia(models.Model):
    TIPO_VOTACAO_CHOICES, SIMBOLICA, NOMINAL, SECRETA = make_choices(
        1, _('Simbólica'),
        2, _('Nominal'),
        3, _('Secreta'),
    )

    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    materia = models.ForeignKey(MateriaLegislativa)
    data_ordem = models.DateField(verbose_name=_('Data da Sessão'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Ementa'))
    numero_ordem = models.PositiveIntegerField(verbose_name=_('Nº Ordem'))
    resultado = models.TextField(blank=True)
    tipo_votacao = models.PositiveIntegerField(
        verbose_name=_('Tipo de votação'), choices=TIPO_VOTACAO_CHOICES)
    votacao_aberta = models.NullBooleanField(
        blank=True,
        choices=YES_NO_CHOICES,
        verbose_name=_('Votação iniciada?'))

    class Meta:
        abstract = True

    def __str__(self):
        return '%s - %s' % (self.numero_ordem, self.sessao_plenaria)


class ExpedienteMateria(AbstractOrdemDia):

    class Meta:
        verbose_name = _('Matéria do Expediente')
        verbose_name_plural = _('Matérias do Expediente')
        ordering = ['numero_ordem']


class TipoExpediente(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_('Tipo'))

    class Meta:
        verbose_name = _('Tipo de Expediente')
        verbose_name_plural = _('Tipos de Expediente')

    def __str__(self):
        return self.nome


class ExpedienteSessao(models.Model):  # ExpedienteSessaoPlenaria
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    tipo = models.ForeignKey(TipoExpediente)
    conteudo = models.TextField(
        blank=True, verbose_name=_('Conteúdo do expediente'))

    class Meta:
        verbose_name = _('Expediente de Sessão Plenaria')
        verbose_name_plural = _('Expedientes de Sessão Plenaria')

    def __str__(self):
        return '%s - %s' % (self.tipo, self.sessao_plenaria)


class IntegranteMesa(models.Model):  # MesaSessaoPlenaria
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    cargo = models.ForeignKey(CargoMesa)
    parlamentar = models.ForeignKey(Parlamentar)

    class Meta:
        verbose_name = _('Participação em Mesa de Sessão Plenaria')
        verbose_name_plural = _('Participações em Mesas de Sessão Plenaria')

    def __str__(self):
        return '%s - %s' % (self.cargo, self.parlamentar)


class AbstractOrador(models.Model):  # Oradores
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar, verbose_name=_('Parlamentar'))
    numero_ordem = models.PositiveIntegerField(
        verbose_name=_('Ordem de pronunciamento'))
    url_discurso = models.CharField(
        max_length=150, blank=True, verbose_name=_('URL Vídeo'))

    class Meta:
        abstract = True

    def __str__(self):
        return _('%(nome)s (%(numero)sº orador)') % {
            'nome': self.parlamentar,
            'numero': self.numero_ordem}


class Orador(AbstractOrador):  # Oradores

    class Meta:
        verbose_name = _('Orador das Explicações Pessoais')
        verbose_name_plural = _('Oradores das Explicações Pessoais')


class OradorExpediente(AbstractOrador):  # OradoresExpediente

    class Meta:
        verbose_name = _('Orador do Expediente')
        verbose_name_plural = _('Oradores do Expediente')


class OrdemDia(AbstractOrdemDia):

    class Meta:
        verbose_name = _('Matéria da Ordem do Dia')
        verbose_name_plural = _('Matérias da Ordem do Dia')
        ordering = ['numero_ordem']


class PresencaOrdemDia(models.Model):  # OrdemDiaPresenca
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)

    class Meta:
        verbose_name = _('Presença da Ordem do Dia')
        verbose_name_plural = _('Presenças da Ordem do Dia')
        ordering = ['parlamentar__nome_parlamentar']

    def __str__(self):
        # FIXME ambigous
        return _('Sessão: %(sessao)s Parlamentar: %(parlamentar)s') % {
            'sessao': self.sessao_plenaria,
            'parlamentar': self.parlamentar}


class TipoResultadoVotacao(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_('Tipo'))

    class Meta:
        verbose_name = _('Tipo de Resultado de Votação')
        verbose_name_plural = _('Tipos de Resultado de Votação')

    def __str__(self):
        return self.nome


class RegistroVotacao(models.Model):
    tipo_resultado_votacao = models.ForeignKey(
        TipoResultadoVotacao, verbose_name=_('Resultado da Votação'))
    materia = models.ForeignKey(MateriaLegislativa)
    ordem = models.ForeignKey(OrdemDia, blank=True, null=True)
    expediente = models.ForeignKey(ExpedienteMateria, blank=True, null=True)
    numero_votos_sim = models.PositiveIntegerField(verbose_name=_('Sim'))
    numero_votos_nao = models.PositiveIntegerField(verbose_name=_('Não'))
    numero_abstencoes = models.PositiveIntegerField(
        verbose_name=_('Abstenções'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observações'))

    class Meta:
        verbose_name = _('Votação')
        verbose_name_plural = _('Votações')

    def __str__(self):
        return _('Ordem: %(ordem)s - Votação: %(votacao)s - '
                 'Matéria: %(materia)s') % {
                     'ordem': self.ordem,
                     'votacao': self.tipo_resultado_votacao,
            'materia': self.materia}


class VotoParlamentar(models.Model):  # RegistroVotacaoParlamentar
    votacao = models.ForeignKey(RegistroVotacao)
    parlamentar = models.ForeignKey(Parlamentar)
    # XXX change to restricted choices
    voto = models.CharField(max_length=10)

    class Meta:
        verbose_name = _('Registro de Votação de Parlamentar')
        verbose_name_plural = _('Registros de Votações de Parlamentares')

    def __str__(self):
        return _('Votação: %(votacao)s - Parlamentar: %(parlamentar)s') % {
            'votacao': self.votacao, 'parlamentar': self.parlamentar}


class SessaoPlenariaPresenca(models.Model):
    sessao_plenaria = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    data_sessao = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = _('Presença em Sessão Plenária')
        verbose_name_plural = _('Presenças em Sessões Plenárias')
        ordering = ['parlamentar__nome_parlamentar']


class AcompanharMateria(models.Model):
    usuario = models.CharField(max_length=50)
    email = models.CharField(
        max_length=50, verbose_name=_('Endereço de email'))
    data_cadastro = models.DateField(auto_now_add=True)
    materia_cadastrada = models.ForeignKey(MateriaLegislativa)
