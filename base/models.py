# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _


class CasaLegislativa(models.Model):
    # TODO ajustar todos os max_length !!!!
    # cod_casa => id (pk)
    nome = models.CharField(max_length=100, verbose_name=_(u'Nome'))
    sigla = models.CharField(max_length=100, verbose_name=_(u'Sigla'))
    endereco = models.CharField(max_length=100, verbose_name=_(u'Endereço'))
    cep = models.CharField(max_length=100, verbose_name=_(u'CEP'))
    municipio = models.CharField(max_length=100, verbose_name=_(u'Município'))
    uf = models.CharField(max_length=100, verbose_name=_(u'UF'))
    telefone = models.CharField(max_length=100, verbose_name=_(u'Telefone'))
    fax = models.CharField(max_length=100, verbose_name=_(u'Fax'))
    cor_fundo = models.CharField(max_length=100, verbose_name=_(u'Cor de fundo'))
    cor_borda = models.CharField(max_length=100, verbose_name=_(u'Cor da borda'))
    cor_principal = models.CharField(max_length=100, verbose_name=_(u'Cor principal'))
    logotipo = models.CharField(max_length=100, verbose_name=_(u'Logotipo'))
    endereco_web = models.CharField(max_length=100, verbose_name=_(u'HomePage'))
    email = models.CharField(max_length=100, verbose_name=_(u'E-mail'))
    informacao_geral = models.CharField(max_length=100, verbose_name=_(u'Informação Geral'))

    class Meta:
        verbose_name = _(u'Casa Legislativa')
        verbose_name_plural = _(u'Casas Legislativas')
