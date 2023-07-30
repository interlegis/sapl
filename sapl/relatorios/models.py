from django.db import models
from django.utils.translation import ugettext_lazy as _
from sapl.utils import YES_NO_CHOICES


class RelatorioConfig(models.Model):
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))
    url = models.CharField(max_length=200, verbose_name=_('URL'))
    publico = models.BooleanField(db_index=True,
                                  default=True,
                                  choices=YES_NO_CHOICES,
                                  verbose_name=_('Público'))
    privado = models.BooleanField(db_index=True,
                                  default=True,
                                  choices=YES_NO_CHOICES,
                                  verbose_name=_('Público'))

    class Meta:
        verbose_name = _('Configuração de Relatório')
        verbose_name_plural = _('Configurações de Relatórios')
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.url}"
