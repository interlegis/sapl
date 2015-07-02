# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _


class CasaLegislativa(models.Model):
    # TODO ajustar todos os max_length !!!!
    # cod_casa => id (pk)
    nome = models.CharField(max_length=100, verbose_name=_(u'Nome'))                      # nom_casa
    sigla = models.CharField(max_length=100, verbose_name=_(u'Sigla'))                     # sgl_casa
    endereco = models.CharField(max_length=100, verbose_name=_(u'Endereço'))                  # end_casa
    cep = models.CharField(max_length=100, verbose_name=_(u'CEP'))                        # num_cep
    municipio = models.CharField(max_length=100, verbose_name=_(u'Município'))                # municipio
    uf = models.CharField(max_length=100, verbose_name=_(u'UF'))                          # sgl_uf
    telefone = models.CharField(max_length=100, verbose_name=_(u'Telefone'))                   # num_tel
    fax = models.CharField(max_length=100, verbose_name=_(u'Fax'))                        # num_fax
    cor_fundo = models.CharField(max_length=100, verbose_name=_(u'Cor de fundo'))             # cor_fundo
    cor_borda = models.CharField(max_length=100, verbose_name=_(u'Cor da borda'))             # cor_borda
    cor_principal = models.CharField(max_length=100, verbose_name=_(u'Cor principal'))        # cor_principal
    logotipo = models.CharField(max_length=100, verbose_name=_(u'Logotipo'))                  # nom_logo
    endereco_web = models.CharField(max_length=100, verbose_name=_(u'HomePage'))              # end_web_casa
    email = models.CharField(max_length=100, verbose_name=_(u'E-mail'))              # end_email_casa
    informacao_geral = models.CharField(max_length=100, verbose_name=_(u'Informação Geral'))  # informacao_geral

    class Meta:
        verbose_name = _(u'Casa Legislativa')
        verbose_name_plural = _(u'Casas Legislativas')
