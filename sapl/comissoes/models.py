import reversion
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from sapl.base.models import Autor
from sapl.parlamentares.models import Parlamentar
from sapl.utils import (YES_NO_CHOICES, SaplGenericRelation,
                        restringe_tipos_de_arquivo_txt, texto_upload_path)


@reversion.register()
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


@reversion.register()
class Comissao(models.Model):
    tipo = models.ForeignKey(TipoComissao,
                             on_delete=models.PROTECT,
                             verbose_name=_('Tipo'))
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))
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
        max_length=15, blank=True,
        verbose_name=_('Tel. Sala Reunião'))
    endereco_secretaria = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Endereço Secretaria'))
    telefone_secretaria = models.CharField(
        max_length=15, blank=True,
        verbose_name=_('Tel. Secretaria'))
    fax_secretaria = models.CharField(
        max_length=15, blank=True, verbose_name=_('Fax Secretaria'))
    agenda_reuniao = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Data/Hora Reunião'))
    local_reuniao = models.CharField(
        max_length=100, blank=True, verbose_name=_('Local Reunião'))
    finalidade = models.TextField(
        blank=True, verbose_name=_('Finalidade'))
    email = models.EmailField(max_length=100,
                              blank=True,
                              verbose_name=_('E-mail'))
    unidade_deliberativa = models.BooleanField(
        choices=YES_NO_CHOICES,
        verbose_name=_('Unidade Deliberativa'))
    ativa = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Comissão Ativa?'))
    autor = SaplGenericRelation(Autor,
                                related_query_name='comissao_set',
                                fields_search=(
                                    ('nome', '__icontains'),
                                    ('sigla', '__icontains')
                                ))

    class Meta:
        verbose_name = _('Comissão')
        verbose_name_plural = _('Comissões')
        ordering = ['nome']

    def __str__(self):
        return self.sigla + ' - ' + self.nome


@reversion.register()
class Periodo(models.Model):  # PeriodoCompComissao
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim'))

    class Meta:
        verbose_name = _('Período de composição de Comissão')
        verbose_name_plural = _('Períodos de composição de Comissão')

    def __str__(self):
        if self.data_inicio and self.data_fim:
            return '%s - %s' % (self.data_inicio.strftime("%d/%m/%Y"),
                                self.data_fim.strftime("%d/%m/%Y"))
        else:
            return '-'


@reversion.register()
class CargoComissao(models.Model):
    nome = models.CharField(max_length=50, verbose_name=_('Cargo'))
    unico = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Único'))

    class Meta:
        verbose_name = _('Cargo de Comissão')
        verbose_name_plural = _('Cargos de Comissão')

    def __str__(self):
        return self.nome


@reversion.register()
class Composicao(models.Model):  # IGNORE
    comissao = models.ForeignKey(Comissao,
                                 on_delete=models.PROTECT,
                                 verbose_name=_('Comissão'))
    periodo = models.ForeignKey(Periodo,
                                on_delete=models.PROTECT,
                                verbose_name=_('Período'))

    class Meta:
        verbose_name = _('Composição de Comissão')
        verbose_name_plural = _('Composições de Comissão')

    def __str__(self):
        return '%s: %s' % (self.comissao.sigla, self.periodo)


@reversion.register()
class Participacao(models.Model):  # ComposicaoComissao
    composicao = models.ForeignKey(Composicao,
                                   related_name='participacao_set',
                                   on_delete=models.PROTECT,
                                   verbose_name=_('Composição'))
    parlamentar = models.ForeignKey(Parlamentar,
                                    on_delete=models.PROTECT,
                                    verbose_name='Parlamentar')
    cargo = models.ForeignKey(CargoComissao,
                              on_delete=models.PROTECT,
                              verbose_name='Cargo')
    titular = models.BooleanField(
        verbose_name=_('Titular'),
        default=False,
        choices=YES_NO_CHOICES)
    data_designacao = models.DateField(verbose_name=_('Data Designação'))
    data_desligamento = models.DateField(blank=True,
                                         null=True,
                                         verbose_name=_('Data Desligamento'))
    motivo_desligamento = models.CharField(
        max_length=150, blank=True,
        verbose_name=_('Motivo Desligamento'))
    observacao = models.CharField(
        max_length=150, blank=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Participação em Comissão')
        verbose_name_plural = _('Participações em Comissão')

    def __str__(self):
        return '%s : %s' % (self.cargo, self.parlamentar)


def get_comissao_media_path(instance, subpath, filename):
    return './sapl/comissao/%s/%s/%s' % (instance.numero, subpath, filename)

def pauta_upload_path(instance, filename):

    return texto_upload_path(instance, filename, subpath='pauta', pk_first=True)

def ata_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='ata', pk_first=True)

def anexo_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='anexo', pk_first=True)


class Reuniao(models.Model):
    periodo = models. ForeignKey(
        Periodo,
        on_delete=models.PROTECT,
        verbose_name=_('Periodo da Composicão da Comissão'))
    comissao = models.ForeignKey(
        Comissao,
        on_delete=models.PROTECT,
        verbose_name=_('Comissão'))
    tipo = models.ForeignKey(
        TipoComissao,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Comissão'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    nome = models.CharField(
        max_length=100, verbose_name=_('Nome da Reunião'))
    tema = models.CharField(
        max_length=100, verbose_name=_('Tema da Reunião'))
    data = models.DateField(verbose_name=_('Data'))
    hora_inicio = models.TimeField(
        verbose_name=_('Horário de Início (hh:mm)'))
    hora_fim = models.TimeField(
        verbose_name=_('Horário de Término (hh:mm)'))
    local_reuniao = models.CharField(
        max_length=100, blank=True, verbose_name=_('Local da Reunião'))
    observacao = models.TextField(
        max_length=150, blank=True, verbose_name=_('Observação'))
    url_audio = models.URLField(
<<<<<<< HEAD
        max_length=150, blank=True,
        verbose_name=_('URL do Arquivo de Áudio (Formatos MP3 / AAC)'))
    url_video = models.URLField(
        max_length=150, blank=True,
        verbose_name=_('URL do Arquivo de Vídeo (Formatos MP4 / FLV / WebM)'))
=======
        max_length=150, blank=True, null=True,
        verbose_name=_('URL Arquivo Áudio (Formatos MP3 / AAC)'))
    url_video = models.URLField(
        max_length=150, blank=True, null=True,
        verbose_name=_('URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)'))
>>>>>>> Corrige Createview e Listview
    upload_pauta = models.FileField(
        blank=True, null=True,
        upload_to=pauta_upload_path,
        verbose_name=_('Pauta da Reunião'),
        validators=[restringe_tipos_de_arquivo_txt])
    upload_ata = models.FileField(
        blank=True, null=True,
        upload_to=ata_upload_path,
        verbose_name=_('Ata da Reunião'),
        validators=[restringe_tipos_de_arquivo_txt])
    upload_anexo = models.FileField(
        blank=True, null=True,
        upload_to=anexo_upload_path,
        verbose_name=_('Anexo da Reunião'))

    class Meta:
        verbose_name = _('Reunião de Comissão')
        verbose_name_plural = _('Reuniões de Comissão')

    def __str__(self):
        return self.nome

    def delete(self, using=None, keep_parents=False):
        if self.upload_pauta:
            self.upload_pauta.delete()

        if self.upload_ata:
            self.upload_ata.delete()

        if self.upload_anexo:
            self.upload_anexo.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

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
