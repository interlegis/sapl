import re

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from sapl.base.models import Autor, AppConfig as SaplAppConfig
from sapl.materia.models import TipoMateriaLegislativa, UnidadeTramitacao,\
    MateriaLegislativa
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES, texto_upload_path,
                        get_settings_auth_user_model,
                        OverwriteStorage)


class TipoDocumentoAdministrativo(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Documento Administrativo')
        verbose_name_plural = _('Tipos de Documento Administrativo')
        ordering = ['descricao']

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


class Protocolo(models.Model):
    numero = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name=_('Número de Protocolo'))
    ano = models.PositiveSmallIntegerField(
        blank=False,
        null=False,
        choices=RANGE_ANOS,
        verbose_name=_('Ano do Protocolo'))
    data = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Data do Protocolo'),
        help_text=_('Informado manualmente'))
    hora = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Hora do Protocolo'),
        help_text=_('Informado manualmente'))
    timestamp_data_hora_manual = models.DateTimeField(default=timezone.now)
    user_data_hora_manual = models.CharField(
        max_length=256,
        blank=True,
        verbose_name=_('IP'),
        help_text=_('Usuário que está realizando Protocolo e informando data e hora manualmente.'))
    ip_data_hora_manual = models.CharField(
        max_length=256,
        blank=True,
        verbose_name=_('IP'),
        help_text=_('Endereço IP da estação de trabalho do usuário que está realizando Protocolo e '
                    'informando data e hora manualmente.'))
    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Usuário'),
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    de_proposicao = models.BooleanField(default=False)
    # Não foi utilizado auto_now_add=True em timestamp porque ele usa
    # datetime.now que não é timezone aware.
    timestamp = models.DateTimeField(
        null=True,
        blank=True,
        default=timezone.now)
    tipo_protocolo = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Tipo de Protocolo'))
    tipo_processo = models.PositiveIntegerField()
    interessado = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Interessado'))
    autor = models.ForeignKey(
        Autor,
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    assunto_ementa = models.TextField(blank=True)
    tipo_documento = models.ForeignKey(
        TipoDocumentoAdministrativo,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Documento'))
    tipo_materia = models.ForeignKey(
        TipoMateriaLegislativa,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Matéria'))
    numero_paginas = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Número de Páginas'))
    observacao = models.TextField(blank=True, verbose_name=_('Observação'))
    anulado = models.BooleanField(default=False)
    user_anulacao = models.CharField(max_length=20, blank=True)
    ip_anulacao = models.CharField(max_length=15, blank=True)
    justificativa_anulacao = models.CharField(
        max_length=260,
        blank=True,
        verbose_name=_('Motivo'))
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Protocolo')
        verbose_name_plural = _('Protocolos')
        ordering = ('id',)
        permissions = (
            ('action_anular_protocolo', _('Permissão para Anular Protocolo')),
        )
        unique_together = ('numero', 'ano',)

    def __str__(self):
        return _('%(numero)s/%(ano)s') % {
            'numero': self.numero, 'ano': self.ano
        }


class DocumentoAdministrativo(models.Model):
    tipo = models.ForeignKey(
        TipoDocumentoAdministrativo, on_delete=models.PROTECT,
        verbose_name=_('Tipo Documento'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))

    complemento = models.CharField(max_length=10, blank=True,
                                   verbose_name=_('Complemento'))

    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    protocolo = models.ForeignKey(
        Protocolo,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Protocolo'))
    data = models.DateField(verbose_name=_('Data'))

    interessado = models.CharField(
        max_length=50, blank=True, verbose_name=_('Interessado'))
    autor = models.ForeignKey(Autor, blank=True, null=True,
                              on_delete=models.PROTECT, verbose_name=_('Autoria'))
    dias_prazo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Dias Prazo'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    tramitacao = models.BooleanField(
        verbose_name=_('Em Tramitação?'),
        choices=YES_NO_CHOICES,
        default=False)
    assunto = models.TextField(verbose_name=_('Assunto'))
    numero_externo = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Número Externo'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    texto_integral = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        storage=OverwriteStorage(),
        upload_to=texto_upload_path,
        verbose_name=_('Texto Integral'))
    restrito = models.BooleanField(default=False,
                                   verbose_name=_('Acesso Restrito'),
                                   blank=True)

    anexados = models.ManyToManyField(
        'self',
        blank=True,
        through='Anexado',
        symmetrical=False,
        related_name='anexo_de',
        through_fields=(
            'documento_principal',
            'documento_anexado'
        )
    )

    materiasvinculadas = models.ManyToManyField(
        MateriaLegislativa,
        blank=True,
        through='VinculoDocAdminMateria',
        related_name='docadmvinculados',
        through_fields=(
            'documento',
            'materia'
        )
    )

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Usuário'),
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    ip = models.CharField(
        verbose_name=_('IP'),
        max_length=60,
        blank=True,
        default=''
    )
    ultima_edicao = models.DateTimeField(
        verbose_name=_('Data e Hora da Edição'),
        blank=True, null=True
    )

    class Meta:
        verbose_name = _('Documento Administrativo')
        verbose_name_plural = _('Documentos Administrativos')
        ordering = ('ano', 'numero', 'id',)

    @classmethod
    def mask_to_str(cls, values, mask):
        erro = set()
        pattern = '({[^{}]+}|{[ /.-]*})'
        campos_escolhidos = re.findall(pattern, mask)
        campos_permitidos = {
            '{.}', '{/}', '{-}',
            '{sigla}',
            '{nome}',
            '{numero}',
            '{ano}',
            '{complemento}',
            '{assunto}',
        }
        condicionais = {
            '{.}': '.',
            '{/}': '/',
            '{-}': '-',
        }

        erro = set(campos_escolhidos) - campos_permitidos

        if erro:
            mask = '{sigla} Nº {numero}/{ano}{-}{complemento} - {nome}'
            campos_escolhidos = re.findall(pattern, mask)

        for i, k in enumerate(campos_escolhidos):
            if k in values.keys():
                if i > 0 and campos_escolhidos[i - 1] in condicionais:
                    mask = mask.replace(
                        campos_escolhidos[i - 1],
                        condicionais[campos_escolhidos[i - 1]]if values[k] else '', 1)
                mask = mask.replace(k, values[k], 1)
            elif k in condicionais:
                if i > 0 and campos_escolhidos[i - 1] in condicionais:
                    mask = mask.replace(
                        campos_escolhidos[i - 1],
                        '', 1)
                if i + 1 == len(campos_escolhidos):
                    mask = mask.replace(k, '', 1)

        return mask, erro

    @cached_property
    def _identificacao_de_documento(self):
        mask = SaplAppConfig.attr('identificacao_de_documentos')

        values = {
            '{sigla}': self.tipo.sigla,
            '{nome}': self.tipo.descricao,
            '{numero}': f'{self.numero:0>3}',
            '{ano}': f'{self.ano}',
            '{complemento}': self.complemento,
            '{assunto}': self.assunto
        }

        return DocumentoAdministrativo.mask_to_str(values, mask)[0]

    def __str__(self):
        return self._identificacao_de_documento

    @property
    def epigrafe(self):
        return str(self)

    def delete(self, using=None, keep_parents=False):
        texto_integral = self.texto_integral
        result = super().delete(using=using, keep_parents=keep_parents)

        if texto_integral:
            texto_integral.delete(save=False)

        return result

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_integral:
            texto_integral = self.texto_integral
            self.texto_integral = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_integral = texto_integral

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class DocumentoAcessorioAdministrativo(models.Model):
    documento = models.ForeignKey(DocumentoAdministrativo,
                                  on_delete=models.PROTECT)
    tipo = models.ForeignKey(
        TipoDocumentoAdministrativo,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo'))
    nome = models.CharField(max_length=30, verbose_name=_('Nome'))
    arquivo = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        upload_to=texto_upload_path,
        storage=OverwriteStorage(),
        verbose_name=_('Arquivo'))
    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))
    autor = models.CharField(
        max_length=200, blank=True, verbose_name=_('Autor'))
    assunto = models.TextField(
        blank=True, verbose_name=_('Assunto'))
    indexacao = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Documento Acessório')
        verbose_name_plural = _('Documentos Acessórios')
        ordering = ('data', 'id')

    def __str__(self):
        return self.nome

    def delete(self, using=None, keep_parents=False):
        arquivo = self.arquivo
        result = super().delete(using=using, keep_parents=keep_parents)

        if arquivo:
            arquivo.delete(save=False)

        return result

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.arquivo = arquivo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


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
        ordering = ('id',)

    def __str__(self):
        return self.descricao


class TramitacaoAdministrativo(models.Model):
    status = models.ForeignKey(
        StatusTramitacaoAdministrativo,
        on_delete=models.PROTECT,
        verbose_name=_('Status'))
    documento = models.ForeignKey(DocumentoAdministrativo,
                                  on_delete=models.PROTECT)
    timestamp = models.DateTimeField(default=timezone.now)
    data_tramitacao = models.DateField(
        verbose_name=_('Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(
        UnidadeTramitacao,
        related_name='adm_tramitacoes_origem',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Local'))
    data_encaminhamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(
        UnidadeTramitacao,
        related_name='adm_tramitacoes_destino',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Destino'))
    urgente = models.BooleanField(verbose_name=_('Urgente ?'),
                                  choices=YES_NO_CHOICES,
                                  default=False)
    texto = models.TextField(verbose_name=_('Texto da Ação'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim do Prazo'))
    user = models.ForeignKey(get_settings_auth_user_model(),
                             verbose_name=_('Usuário'),
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True)
    ip = models.CharField(verbose_name=_('IP'),
                          max_length=60,
                          blank=True,
                          default='')
    ultima_edicao = models.DateTimeField(
        verbose_name=_('Data e Hora da Edição'),
        blank=True, null=True
    )

    class Meta:
        verbose_name = _('Tramitação de Documento Administrativo')
        verbose_name_plural = _('Tramitações de Documento Administrativo')
        ordering = ('id',)

    def __str__(self):
        return _('%(documento)s - %(status)s') % {
            'documento': self.documento, 'status': self.status
        }


class Anexado(models.Model):
    documento_principal = models.ForeignKey(
        DocumentoAdministrativo, related_name='documento_principal_set',
        on_delete=models.CASCADE,
        verbose_name=_('Documento Principal')
    )
    documento_anexado = models.ForeignKey(
        DocumentoAdministrativo, related_name='documento_anexado_set',
        on_delete=models.CASCADE,
        verbose_name=_('Documento Anexado')
    )
    data_anexacao = models.DateField(verbose_name=_('Data Anexação'))
    data_desanexacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desanexação')
    )

    class Meta:
        verbose_name = _('Anexado')
        verbose_name_plural = _('Anexados')
        ordering = ('id',)

    def __str__(self):
        return _('Anexado: %(documento_anexado_tipo)s %(documento_anexado_numero)s'
                 '/%(documento_anexado_ano)s\n') % {
                     'documento_anexado_tipo': self.documento_anexado.tipo,
                     'documento_anexado_numero': self.documento_anexado.numero,
                     'documento_anexado_ano': self.documento_anexado.ano
        }


class VinculoDocAdminMateria(models.Model):
    documento = models.ForeignKey(
        DocumentoAdministrativo, related_name='materialegislativa_vinculada_set',
        on_delete=models.CASCADE,
        verbose_name=_('Documento Administrativo')
    )
    materia = models.ForeignKey(
        MateriaLegislativa, related_name='documentoadministrativo_vinculado_set',
        on_delete=models.CASCADE,
        verbose_name=_('Matéria Legislativa')
    )
    data_anexacao = models.DateField(verbose_name=_('Data Anexação'))
    data_desanexacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desanexação')
    )

    class Meta:
        verbose_name = _(
            'Vinculo entre Documento Administrativo e Matéria Legislativa')
        verbose_name_plural = _(
            'Vinculos entre Documento Administrativo e Matéria Legislativa')
        ordering = ('id',)
        unique_together = (
            ('documento', 'materia'),
        )

    def __str__(self):
        return f'Vinculo: {self.documento} - {self.materia}'


class AcompanhamentoDocumento(models.Model):
    usuario = models.CharField(max_length=50)
    documento = models.ForeignKey(
        DocumentoAdministrativo, on_delete=models.CASCADE)
    email = models.EmailField(
        max_length=100, verbose_name=_('E-mail'))
    data_cadastro = models.DateField(auto_now_add=True)
    hash = models.CharField(max_length=8)
    confirmado = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Acompanhamento de Documento')
        verbose_name_plural = _('Acompanhamentos de Documento')
        ordering = ('id',)

    def __str__(self):
        if self.data_cadastro is None:
            return _('%(documento)s - %(email)s') % {
                'documento': self.documento,
                'email': self.email
            }
        else:
            return _('%(documento)s - %(email)s - Registrado em: %(data)s') % {
                'documento': self.documento,
                'email': self.email,
                'data': str(self.data_cadastro.strftime('%d/%m/%Y'))
            }
