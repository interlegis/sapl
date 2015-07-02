# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _


class LexmlProvedor(models.Model):  # LexmlRegistroProvedor
    id_provedor = models.IntegerField(verbose_name=_(u'Id do provedor'))                                                # id_provedor
    nome = models.CharField(max_length=255, verbose_name=_(u'Nome do provedor'))                               # nom_provedor
    sigla = models.CharField(max_length=15)                                                                    # sgl_provedor
    email_responsavel = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'E-mail do responsável'))        # adm_email
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True, verbose_name=_(u'Nome do responsável'))  # nom_responsavel
    tipo = models.CharField(max_length=50)                                                                              # tipo
    id_responsavel = models.IntegerField(blank=True, null=True, verbose_name=_(u'Id do responsável'))                   # id_responsavel
    xml = models.TextField(blank=True, null=True, verbose_name=_(u'XML fornecido pela equipe do LexML:'))      # xml_provedor

    class Meta:
        verbose_name = _(u'Provedor Lexml')
        verbose_name_plural = _(u'Provedores Lexml')


class LexmlRegistroPublicador(models.Model):
    id_publicador = models.IntegerField(verbose_name=_(u'Id do publicador'))                                            # id_publicador
    nome = models.CharField(max_length=255, verbose_name=_(u'Nome do publicador'))                           # nom_publicador
    email_responsavel = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'E-mail do responsável'))        # adm_email
    sigla = models.CharField(max_length=255, blank=True, null=True, verbose_name=_(u'Sigla do Publicador'))                                                     # sigla
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True, verbose_name=_(u'Nome do responsável'))  # nom_responsavel
    tipo = models.CharField(max_length=50)                                                                              # tipo
    id_responsavel = models.IntegerField(verbose_name=_(u'Id do responsável'))                                          # id_responsavel

    class Meta:
        verbose_name = _(u'Publicador Lexml')
        verbose_name_plural = _(u'Publicadores Lexml')
