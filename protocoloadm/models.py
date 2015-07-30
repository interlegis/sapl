from django.db import models
from django.utils.translation import ugettext_lazy as _

from materia.models import Autor, TipoMateriaLegislativa, UnidadeTramitacao
from sapl.utils import make_choices


class TipoDocumentoAdministrativo(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Documento Administrativo')
        verbose_name_plural = _('Tipos de Documento Administrativo')

    def __str__(self):
        return self.descricao


class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(
        TipoDocumentoAdministrativo, verbose_name=_('Tipo Documento'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'))
    data = models.DateField(verbose_name=_('Data'))
    numero_protocolo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Núm. Protocolo'))
    interessado = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_('Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True)
    dias_prazo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Dias Prazo'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    tramitacao = models.BooleanField(verbose_name=_('Em Tramitação?'))
    assunto = models.TextField(verbose_name=_('Assunto'))
    observacao = models.TextField(
        blank=True, null=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Documento Administrativo')
        verbose_name_plural = _('Documentos Administrativos')

    def __str__(self):
        return _('%(tipo)s - %(assunto)s') % {
            'tipo': self.tipo, 'assunto': self.assunto
        }


class DocumentoAcessorioAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo)
    tipo = models.ForeignKey(
        TipoDocumentoAdministrativo, verbose_name=_('Tipo'))
    nome = models.CharField(max_length=30, verbose_name=_('Nome'))
    arquivo = models.CharField(max_length=100, verbose_name=_('Arquivo'))
    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))
    autor = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_('Autor'))
    assunto = models.TextField(
        blank=True, null=True, verbose_name=_('Assunto'))
    indexacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Documento Acessório')
        verbose_name_plural = _('Documentos Acessórios')

    def __str__(self):
        return self.nome


class Protocolo(models.Model):
    numero = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número do Protocolo'))
    ano = models.PositiveSmallIntegerField()
    data = models.DateField()
    hora = models.TimeField()
    timestamp = models.DateTimeField()
    tipo_protocolo = models.PositiveIntegerField(
        verbose_name=_('Tipo de Protocolo'))
    tipo_processo = models.PositiveIntegerField()
    interessado = models.CharField(
        max_length=60, blank=True, null=True, verbose_name=_('Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True)
    assunto_ementa = models.TextField(blank=True, null=True)
    tipo_documento = models.ForeignKey(
        TipoDocumentoAdministrativo,
        blank=True,
        null=True,
        verbose_name=_('Tipo de documento'))
    tipo_materia = models.ForeignKey(
        TipoMateriaLegislativa,
        blank=True,
        null=True,
        verbose_name=_('Tipo Matéria'))
    numero_paginas = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número de Páginas'))
    observacao = models.TextField(
        blank=True, null=True, verbose_name=_('Observação'))
    anulado = models.BooleanField()
    user_anulacao = models.CharField(max_length=20, blank=True, null=True)
    ip_anulacao = models.CharField(max_length=15, blank=True, null=True)
    justificativa_anulacao = models.CharField(
        max_length=60, blank=True, null=True)
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Protocolo')
        verbose_name_plural = _('Protocolos')


class StatusTramitacaoAdministrativo(models.Model):
    INDICADOR_CHOICES, FIM, RETORNO = make_choices(
        'F', _('Fim'),
        'R', _('Retorno'),
    )

    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=60, verbose_name=_('Descrição'))
    # TODO make specific migration considering both ind_fim_tramitacao,
    # ind_retorno_tramitacao
    indicador = models.CharField(
        max_length=1, verbose_name=_('Indicador da Tramitação'),
        choices=INDICADOR_CHOICES)

    class Meta:
        verbose_name = _('Status de Tramitação')
        verbose_name_plural = _('Status de Tramitação')

    def __str__(self):
        return self.descricao


class TramitacaoAdministrativo(models.Model):
    status = models.ForeignKey(
        StatusTramitacaoAdministrativo,
        blank=True,
        null=True,
        verbose_name=_('Status'))
    documento = models.ForeignKey(DocumentoAdministrativo)
    data_tramitacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(
        UnidadeTramitacao,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('Unidade Local'))
    data_encaminhamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(
        UnidadeTramitacao,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('Unidade Destino'))
    ultima = models.BooleanField()
    texto = models.TextField(
        blank=True, null=True, verbose_name=_('Texto da Ação'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim do Prazo'))

    class Meta:
        verbose_name = _('Tramitação de Documento Administrativo')
        verbose_name_plural = _('Tramitações de Documento Administrativo')

    def __str__(self):
        return _('%(documento)s - %(status)s') % {
            'documento': self.documento, 'status': self.status
        }
