from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from sapl.base.models import Autor
from sapl.materia.models import TipoMateriaLegislativa, UnidadeTramitacao
from sapl.utils import RANGE_ANOS, YES_NO_CHOICES, texto_upload_path


class TipoDocumentoAdministrativo(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Documento Administrativo')
        verbose_name_plural = _('Tipos de Documento Administrativo')

    def __str__(self):
        return self.descricao


"""
uuid4 + filenames diversos apesar de tornar url de um arquivo praticamente
impossível de ser localizado não está controlando o acesso.
Exemplo: o SAPL está configurado para ser docs adm restritivo porém
alguem resolve perga o link e mostrar o tal arquivo para um amigo, ou um
vizinho de departamento que não possui acesso... ou mesmo alguem que nem ao
menos está logado... este arquivo estará livre

outro caso, um funcionário bem intencionado, mas com um computador infectado
que consegue pegar todos os links da página que ele está acessando e esse
funcionário possui permissão para ver arquivos de docs administrativos.
Consequentemente os arquivos se tornarão públicos pois podem ser acessados
via url sem controle de acesso.

* foi aberta uma issue no github para rever a questão de arquivos privados:
https://github.com/interlegis/sapl/issues/751

a solução dela deverá dar o correto tratamento a essa questão.


def texto_upload_path(instance, filename):
    return '/'.join([instance._meta.model_name, str(uuid4()), filename])
"""


class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(
        TipoDocumentoAdministrativo, verbose_name=_('Tipo Documento'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    data = models.DateField(verbose_name=_('Data'))
    numero_protocolo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Núm. Protocolo'))
    interessado = models.CharField(
        max_length=50, blank=True, verbose_name=_('Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True)
    dias_prazo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Dias Prazo'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    tramitacao = models.BooleanField(
        verbose_name=_('Em Tramitação?'),
        choices=YES_NO_CHOICES)
    assunto = models.TextField(verbose_name=_('Assunto'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    texto_integral = models.FileField(
        blank=True,
        null=True,
        upload_to=texto_upload_path,
        verbose_name=_('Texto Integral'))

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
    arquivo = models.FileField(
        blank=True,
        null=True,
        upload_to=texto_upload_path,
        verbose_name=_('Arquivo'))
    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))
    autor = models.CharField(
        max_length=50, blank=True, verbose_name=_('Autor'))
    assunto = models.TextField(
        blank=True, verbose_name=_('Assunto'))
    indexacao = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Documento Acessório')
        verbose_name_plural = _('Documentos Acessórios')

    def __str__(self):
        return self.nome


class Protocolo(models.Model):
    numero = models.PositiveIntegerField(
        blank=False, null=False, verbose_name=_('Número de Protocolo'))
    ano = models.PositiveSmallIntegerField(blank=False,
                                           null=False,
                                           choices=RANGE_ANOS,
                                           verbose_name=_('Ano do Protocolo'))
    data = models.DateField()
    hora = models.TimeField()
    # TODO transformar campo timestamp em auto_now_add
    timestamp = models.DateTimeField()
    tipo_protocolo = models.PositiveIntegerField(
        verbose_name=_('Tipo de Protocolo'))
    tipo_processo = models.PositiveIntegerField()
    interessado = models.CharField(
        max_length=60, blank=True, verbose_name=_('Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True)
    assunto_ementa = models.TextField(blank=True)
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
        blank=True, verbose_name=_('Observação'))
    anulado = models.BooleanField()
    user_anulacao = models.CharField(max_length=20, blank=True)
    ip_anulacao = models.CharField(max_length=15, blank=True)
    justificativa_anulacao = models.CharField(
        max_length=60, blank=True, verbose_name='Motivo')
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Protocolo')
        verbose_name_plural = _('Protocolos')
        permissions = (
            ('action_anular_protocolo', _('Permissão para Anular Protocolo')),
        )


class StatusTramitacaoAdministrativo(models.Model):
    INDICADOR_CHOICES = Choices(
        ('F', 'fim', _('Fim')),
        ('R', 'retorno', _('Retorno')),
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
        verbose_name=_('Status'))
    documento = models.ForeignKey(DocumentoAdministrativo)
    data_tramitacao = models.DateField(
        verbose_name=_('Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(
        UnidadeTramitacao,
        related_name='adm_tramitacoes_origem',
        verbose_name=_('Unidade Local'))
    data_encaminhamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(
        UnidadeTramitacao,
        related_name='adm_tramitacoes_destino',
        verbose_name=_('Unidade Destino'))
    texto = models.TextField(
        blank=True, verbose_name=_('Texto da Ação'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim do Prazo'))

    class Meta:
        verbose_name = _('Tramitação de Documento Administrativo')
        verbose_name_plural = _('Tramitações de Documento Administrativo')

    def __str__(self):
        return _('%(documento)s - %(status)s') % {
            'documento': self.documento, 'status': self.status
        }
