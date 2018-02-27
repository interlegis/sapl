import reversion
from django.db import models
from django.utils.translation import ugettext_lazy as _


@reversion.register()
class AudienciaPublica(models.Model):
    class Meta:
        verbose_name = _('Audiência Pública')
        verbose_name_plural = _('Audiências Públicas')

    def __str__(self):
        return self.nome
