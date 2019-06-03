import reversion
from django.db import models
from django.utils.translation import ugettext_lazy as _


@reversion.register()
class Painel(models.Model):
    PAINEL_TYPES = (
        ('C', 'Completo'),
        ('P', 'Parlamentares'),
        ('V', 'Votação'),
        ('M', 'Mensagem'),
    )

    aberto = models.BooleanField(verbose_name=_('Abrir painel'), default=False)
    data_painel = models.DateField(verbose_name=_('Data painel'))
    mostrar = models.CharField(max_length=1,
                               choices=PAINEL_TYPES, default='C')

    def __str__(self):
        return str(self.aberto) + ":" + self.data_painel.strftime("%d/%m/%Y")


@reversion.register()
class TipoCronometro(models.Model):
    nome = models.CharField(max_length=30, verbose_name=_('Tipo Cronômetro'))

    class Meta:
        verbose_name = _('Tipo de Cronômetro')
        verbose_name_plural = _('Tipos de Cronômetro')
        ordering = ['nome']

    def __str__(self):
        return self.nome


@reversion.register()
class Cronometro(models.Model):
    CRONOMETRO_TYPES = (
        ('A', _('Aparte')),
        ('D', _('Discurso')),
        ('O', _('Ordem do dia')),
        ('C', _('Considerações finais'))
    )

    CRONOMETRO_STATUS = (
        ('I', 'Start'),
        ('R', 'Reset'),
        ('S', 'Stop'),
        ('C', 'Increment'),
    )

    status = models.CharField(
        max_length=1,
        verbose_name=_('Status do cronômetro'),
        choices=CRONOMETRO_STATUS,
        default='S')
    duracao_cronometro = models.DurationField(
        verbose_name=_('Duração do cronômetro'),
        blank=True,
        null=True)
    # tipo = models.CharField(
    #     max_length=1, choices=CRONOMETRO_TYPES,
    #     verbose_name=_('Tipo Cronômetro'))
    tipo = models.ForeignKey(TipoCronometro,
                             on_delete=models.PROTECT,
                             verbose_name=_('Tipo Cronômetro'))