from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import (CargoMesa, Parlamentar)

from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES, SaplGenericRelation,
                        restringe_tipos_de_arquivo_txt, texto_upload_path,
                        OverwriteStorage)


def get_audiencia_media_path(instance, subpath, filename):
    return './sapl/audiencia/%s/%s/%s' % (instance.numero, subpath, filename)


def pauta_upload_path(instance, filename):
    return texto_upload_path(
        instance, filename, subpath='pauta', pk_first=True)


def ata_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='ata', pk_first=True)


def anexo_upload_path(instance, filename):
    return texto_upload_path(
        instance, filename, subpath='anexo', pk_first=True)


class TipoAudienciaPublica(models.Model):
    TIPO_AUDIENCIA_CHOICES = Choices(('A', 'audiencia', _('Audiência Pública')),
                                     ('P', 'plebiscito', _('Plebiscito')),
                                     ('R', 'referendo', _('Referendo')),
                                     ('I', 'iniciativa', _('Iniciativa Popular')))

    nome = models.CharField(
        max_length=50, verbose_name=_('Nome do Tipo de Audiência Pública'), default='Audiência Pública')
    tipo = models.CharField(
        max_length=1, verbose_name=_('Tipo de Audiência Pública'), choices=TIPO_AUDIENCIA_CHOICES, default='A')

    class Meta:
        verbose_name = _('Tipo de Audiência Pública')
        verbose_name_plural = _('Tipos de Audiência Pública')
        ordering = ['nome']

    def __str__(self):
        return self.nome


class AudienciaPublica(models.Model):
    materia = models.ForeignKey(
        MateriaLegislativa,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Matéria Legislativa'))
    tipo = models.ForeignKey(TipoAudienciaPublica,
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True,
                             verbose_name=_('Tipo de Audiência Pública'))
    numero = models.PositiveIntegerField(blank=True, verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    nome = models.CharField(
        max_length=100, verbose_name=_('Nome da Audiência Pública'))
    tema = models.CharField(
        max_length=100, verbose_name=_('Tema da Audiência Pública'))
    data = models.DateField(verbose_name=_('Data'))
    hora_inicio = models.CharField(
        max_length=5, verbose_name=_('Horário Início(hh:mm)'))
    hora_fim = models.CharField(
        max_length=5, blank=True, verbose_name=_('Horário Fim(hh:mm)'))
    observacao = models.TextField(
        max_length=500, blank=True, verbose_name=_('Observação'))
    audiencia_cancelada = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Audiência Cancelada?'))
    parlamentar_autor = models.ForeignKey(
        Parlamentar,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Parlamentar Autor'))
    requerimento = models.ForeignKey(
        MateriaLegislativa,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('Requerimento da Audiência Pública'),
        related_name=_('requerimento'))
    url_audio = models.URLField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Áudio (Formatos MP3 / AAC)'))
    url_video = models.URLField(
        max_length=150, blank=True,
        verbose_name=_('URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))
    upload_pauta = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        upload_to=pauta_upload_path,
        storage=OverwriteStorage(),
        verbose_name=_('Pauta da Audiência Pública'),
        validators=[restringe_tipos_de_arquivo_txt])
    upload_ata = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        upload_to=ata_upload_path,
        verbose_name=_('Ata da Audiência Pública'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt])
    upload_anexo = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        upload_to=anexo_upload_path,
        storage=OverwriteStorage(),
        verbose_name=_('Anexo da Audiência Pública'))

    class Meta:
        verbose_name = _('Audiência Pública')
        verbose_name_plural = _('Audiências Públicas')
        ordering = ['ano', 'numero', 'nome', 'tipo']

    def __str__(self):
        return self.nome

    def delete(self, using=None, keep_parents=False):
        upload_pauta = self.upload_pauta
        upload_ata = self.upload_ata
        upload_anexo = self.upload_anexo

        result = super().delete(using=using, keep_parents=keep_parents)

        if upload_pauta:
            upload_pauta.delete(save=False)

        if upload_ata:
            upload_ata.delete(save=False)

        if upload_anexo:
            upload_anexo.delete(save=False)

        return result

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and (self.upload_pauta or self.upload_ata or
                            self.upload_anexo):
            upload_pauta = self.upload_pauta
            upload_ata = self.upload_ata
            upload_anexo = self.upload_anexo
            self.upload_pauta = None
            self.upload_ata = None
            self.upload_anexo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)

            self.upload_pauta = upload_pauta
            self.upload_ata = upload_ata
            self.upload_anexo = upload_anexo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class AnexoAudienciaPublica(models.Model):
    audiencia = models.ForeignKey(AudienciaPublica,
                                  on_delete=models.PROTECT)
    arquivo = models.FileField(
        max_length=300,
        upload_to=texto_upload_path,
        storage=OverwriteStorage(),
        verbose_name=_('Arquivo'))
    data = models.DateField(
        auto_now=timezone.now)
    assunto = models.TextField(
        verbose_name=_('Assunto'))

    class Meta:
        verbose_name = _('Anexo de Documento Acessório')
        verbose_name_plural = _('Anexo de Documentos Acessórios')
        ordering = ('id',)

    def __str__(self):
        return self.assunto

    def delete(self, using=None, keep_parents=False):
        arquivo = self.arquivo
        result = super().delete(using=using, keep_parents=keep_parents)

        if arquivo:
            arquivo.delete(save=False)

        return result

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(
                self,
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields)
            self.arquivo = arquivo

        return models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using,
                                 update_fields=update_fields)
