# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _


class LexmlProvedor(models.Model):  # LexmlRegistroProvedor
    id_provedor = models.IntegerField(verbose_name=_(u'Id do provedor'))
    nome = models.CharField(max_length=255, verbose_name=_(u'Nome do provedor'))
    sigla = models.CharField(max_length=15)
    email_responsavel = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'E-mail do responsável'))
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True, verbose_name=_(u'Nome do responsável'))
    tipo = models.CharField(max_length=50)
    id_responsavel = models.IntegerField(blank=True, null=True, verbose_name=_(u'Id do responsável'))
    xml = models.TextField(blank=True, null=True, verbose_name=_(u'XML fornecido pela equipe do LexML:'))

    class Meta:
        verbose_name = _(u'Provedor Lexml')
        verbose_name_plural = _(u'Provedores Lexml')


class LexmlPublicador(models.Model):
    id_publicador = models.IntegerField(verbose_name=_(u'Id do publicador'))
    nome = models.CharField(max_length=255, verbose_name=_(u'Nome do publicador'))
    email_responsavel = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'E-mail do responsável'))
    sigla = models.CharField(max_length=255, blank=True, null=True, verbose_name=_(u'Sigla do Publicador'))
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True, verbose_name=_(u'Nome do responsável'))
    tipo = models.CharField(max_length=50)
    id_responsavel = models.IntegerField(verbose_name=_(u'Id do responsável'))

    class Meta:
        verbose_name = _(u'Publicador Lexml')
        verbose_name_plural = _(u'Publicadores Lexml')
