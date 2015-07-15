from django.db import models
from django.utils.translation import ugettext as _


class CasaLegislativa(models.Model):
    # TODO ajustar todos os max_length !!!!
    # cod_casa => id (pk)
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=100, verbose_name=_('Sigla'))
    endereco = models.CharField(max_length=100, verbose_name=_('Endereço'))
    cep = models.CharField(max_length=100, verbose_name=_('CEP'))
    municipio = models.CharField(max_length=100, verbose_name=_('Município'))
    uf = models.CharField(max_length=100, verbose_name=_('UF'))
    telefone = models.CharField(max_length=100, verbose_name=_('Telefone'))
    fax = models.CharField(max_length=100, verbose_name=_('Fax'))
    cor_fundo = models.CharField(
        max_length=100, verbose_name=_('Cor de fundo'))
    cor_borda = models.CharField(
        max_length=100, verbose_name=_('Cor da borda'))
    cor_principal = models.CharField(
        max_length=100, verbose_name=_('Cor principal'))
    logotipo = models.CharField(max_length=100, verbose_name=_('Logotipo'))
    endereco_web = models.CharField(max_length=100, verbose_name=_('HomePage'))
    email = models.CharField(max_length=100, verbose_name=_('E-mail'))
    informacao_geral = models.CharField(
        max_length=100, verbose_name=_('Informação Geral'))

    class Meta:
        verbose_name = _('Casa Legislativa')
        verbose_name_plural = _('Casas Legislativas')
