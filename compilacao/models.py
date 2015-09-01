from django.db import models
from django.utils.translation import ugettext_lazy as _


class TipoNota(models.Model):
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    modelo = models.TextField(
        blank=True, null=True, verbose_name=_('Modelo'))

    class Meta:
        verbose_name = _('Tipo de Nota')
        verbose_name_plural = _('Tipos de Nota')

    def __str__(self):
        return self.sigla
