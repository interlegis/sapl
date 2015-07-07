# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from materia.models import MateriaLegislativa


class AssuntoNorma(models.Model):
    assunto = models.CharField(max_length=50, verbose_name=_(u'Assunto'))
    descricao = models.CharField(max_length=250, blank=True, null=True, verbose_name=_(u'Descrição'))

    class Meta:
        verbose_name = _(u'Assunto de Norma')
        verbose_name_plural = _(u'Assuntos de Norma')


class TipoNormaJuridica(models.Model):
    # TODO transform into Domain Model and use an FK for the field
    EQUIVALENTE_LEXML_CHOICES = ((name, name) for name in
                                 ('constituicao',
                                  'ementa.constitucional',
                                  'lei.complementar',
                                  'lei.delegada',
                                  'lei',
                                  'decreto.lei',
                                  'medida.provisoria',
                                  'decreto',
                                  'lei.organica',
                                  'emenda.lei.organica',
                                  'decreto.legislativo',
                                  'resolucao',
                                  'regimento.interno',
                                  ))
    equivalente_lexml = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Equivalente LexML'), choices=EQUIVALENTE_LEXML_CHOICES)
    sigla = models.CharField(max_length=3, verbose_name=_(u'Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))

    class Meta:
        verbose_name = _(u'Tipo de Norma Jurídica')
        verbose_name_plural = _(u'Tipos de Norma Jurídica')


class NormaJuridica(models.Model):
    MUNICIPAL = 'M'
    ESTADUAL = 'E'
    FEDERAL = 'F'
    ESFERA_FEDERACAO_CHOICES = ((MUNICIPAL, _(u'Municipal')),
                                (ESTADUAL, _(u'Estadual')),
                                (FEDERAL, _(u'Federal')))

    tipo = models.ForeignKey(TipoNormaJuridica, verbose_name=_(u'Tipo'))
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)
    numero = models.IntegerField(verbose_name=_(u'Número'))
    ano = models.SmallIntegerField(verbose_name=_(u'Ano'))
    esfera_federacao = models.CharField(max_length=1, verbose_name=_(u'Esfera Federação'), choices=ESFERA_FEDERACAO_CHOICES)
    data = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))
    data_publicacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Publicação'))
    veiculo_publicacao = models.CharField(max_length=30, blank=True, null=True, verbose_name=_(u'Veículo Publicação'))
    pagina_inicio_publicacao = models.IntegerField(blank=True, null=True, verbose_name=_(u'Pg. Início'))
    pagina_fim_publicacao = models.IntegerField(blank=True, null=True, verbose_name=_(u'Pg. Fim'))
    ementa = models.TextField(verbose_name=_(u'Ementa'))
    indexacao = models.TextField(blank=True, null=True, verbose_name=_(u'Indexação'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))
    complemento = models.NullBooleanField(blank=True, verbose_name=_(u'Complementar ?'))
    assunto = models.ForeignKey(AssuntoNorma)  # XXX was a CharField (attention on migrate)
    data_vigencia = models.DateField(blank=True, null=True)
    timestamp = models.DateTimeField()

    class Meta:
        verbose_name = _(u'Norma Jurídica')
        verbose_name_plural = _(u'Normas Jurídicas')


class LegislacaoCitada(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    norma = models.ForeignKey(NormaJuridica)
    disposicoes = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Disposição'))
    parte = models.CharField(max_length=8, blank=True, null=True, verbose_name=_(u'Parte'))
    livro = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Livro'))
    titulo = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Título'))
    capitulo = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Capítulo'))
    secao = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Seção'))
    subsecao = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Subseção'))
    artigo = models.CharField(max_length=4, blank=True, null=True, verbose_name=_(u'Artigo'))
    paragrafo = models.CharField(max_length=3, blank=True, null=True, verbose_name=_(u'Parágrafo'))
    inciso = models.CharField(max_length=10, blank=True, null=True, verbose_name=_(u'Inciso'))
    alinea = models.CharField(max_length=3, blank=True, null=True, verbose_name=_(u'Alínea'))
    item = models.CharField(max_length=3, blank=True, null=True, verbose_name=_(u'Item'))

    class Meta:
        verbose_name = _(u'Matéria Legislativa')
        verbose_name_plural = _(u'Matérias Legislativas')


class VinculoNormaJuridica(models.Model):
    TIPO_VINCULO_CHOICES = (
        ('A', u'Altera a norma'),
        ('R', u'Revoga a norma'),
        ('P', u'Revoga parcialmente a norma'),
        ('T', u'Revoga por consolidação a norma'),
        ('C', u'Norma correlata'),
        ('I', u'Suspende a execução da norma'),
        ('G', u'Regulamenta a norma'),
    )

    # TODO M2M ???
    norma_referente = models.ForeignKey(NormaJuridica, related_name='+')
    norma_referida = models.ForeignKey(NormaJuridica, related_name='+')
    tipo_vinculo = models.CharField(max_length=1, blank=True, null=True, choices=TIPO_VINCULO_CHOICES)

    class Meta:
        verbose_name = _(u'Vínculo entre Normas Jurídicas')
        verbose_name_plural = _(u'Vínculos entre Normas Jurídicas')
