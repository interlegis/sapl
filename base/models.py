# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _


class CasaLegislativa(models.Model):
    # TODO ajustar todos os max_length !!!!

    cod_casa = models.CharField(max_length=100, verbose_name=_(u'Código'))                    # cod_casa
    nom_casa = models.CharField(max_length=100, verbose_name=_(u'Nome'))                      # nom_casa
    sgl_casa = models.CharField(max_length=100, verbose_name=_(u'Sigla'))                     # sgl_casa
    end_casa = models.CharField(max_length=100, verbose_name=_(u'Endereço'))                  # end_casa
    num_cep = models.CharField(max_length=100, verbose_name=_(u'CEP'))                        # num_cep
    municipio = models.CharField(max_length=100, verbose_name=_(u'Município'))                # municipio
    sgl_uf = models.CharField(max_length=100, verbose_name=_(u'UF'))                          # sgl_uf
    num_tel = models.CharField(max_length=100, verbose_name=_(u'Telefone'))                   # num_tel
    num_fax = models.CharField(max_length=100, verbose_name=_(u'Fax'))                        # num_fax
    senha_inicial = models.CharField(max_length=100, verbose_name=_(u'Senha'))            # txt_senha_inicial
    cor_fundo = models.CharField(max_length=100, verbose_name=_(u'Cor de fundo'))             # cor_fundo
    cor_borda = models.CharField(max_length=100, verbose_name=_(u'Cor da borda'))             # cor_borda
    cor_principal = models.CharField(max_length=100, verbose_name=_(u'Cor principal'))        # cor_principal
    nom_logo = models.CharField(max_length=100, verbose_name=_(u'Logotipo'))                  # nom_logo
    end_web_casa = models.CharField(max_length=100, verbose_name=_(u'HomePage'))              # end_web_casa
    end_email_casa = models.CharField(max_length=100, verbose_name=_(u'E-mail'))              # end_email_casa
    informacao_geral = models.CharField(max_length=100, verbose_name=_(u'Informação Geral'))  # informacao_geral

    class Meta:
        verbose_name = _(u'Casa Legislativa')
        verbose_name_plural = _(u'Casas Legislativas')
