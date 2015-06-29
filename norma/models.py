# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from materia.models import MateriaLegislativa


class AssuntoNorma(models.Model):
    descricao_assunto = models.CharField(max_length=50, verbose_name=_(u'Assunto'))                              # des_assunto
    descricao_estendida = models.CharField(max_length=250, blank=True, null=True, verbose_name=_(u'Descrição'))  # des_estendida

    class Meta:
        verbose_name = _(u'Assunto de Norma')
        verbose_name_plural = _(u'Assuntos de Norma')


class TipoNormaJuridica(models.Model):
    voc_lexml = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Equivalente LexML'))  # voc_lexml
    sigla_tipo_norma = models.CharField(max_length=3, verbose_name=_(u'Sigla'))                               # sgl_tipo_norma
    descricao_tipo_norma = models.CharField(max_length=50, verbose_name=_(u'Descrição'))                      # des_tipo_norma

    class Meta:
        verbose_name = _(u'Tipo de Norma Jurídica')
        verbose_name_plural = _(u'Tipos de Norma Jurídica')


class NormaJuridica(models.Model):
    tipo = models.ForeignKey(TipoNormaJuridica, verbose_name=_(u'Tipo'))                                                          # tip_norma
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)                                                        # cod_materia
    numero_norma = models.IntegerField(verbose_name=_(u'Número'))                                                                 # num_norma
    ano_norma = models.SmallIntegerField(verbose_name=_(u'Ano'))                                                                  # ano_norma
    tipo_esfera_federacao = models.CharField(max_length=1, verbose_name=_(u'Esfera Federação'))                                   # tip_esfera_federacao
    data_norma = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))                                                 # dat_norma
    data_publicacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Publicação'))                                 # dat_publicacao
    descricao_veiculo_publicacao = models.CharField(max_length=30, blank=True, null=True, verbose_name=_(u'Veículo Publicação'))  # des_veiculo_publicacao
    numero_pag_inicio_publ = models.IntegerField(blank=True, null=True, verbose_name=_(u'Pg. Início'))                            # num_pag_inicio_publ
    numero_pag_fim_publ = models.IntegerField(blank=True, null=True, verbose_name=_(u'Pg. Fim'))                                  # num_pag_fim_publ
    txt_ementa = models.TextField(verbose_name=_(u'Ementa'))                                                                      # txt_ementa
    txt_indexacao = models.TextField(blank=True, null=True, verbose_name=_(u'Indexação'))                                         # txt_indexacao
    txt_observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))                                       # txt_observacao
    complemento = models.NullBooleanField(blank=True, verbose_name=_(u'Complementar ?'))                                          # ind_complemento
    assunto = models.ForeignKey(AssuntoNorma)  # XXX was a CharField (attention on migrate)                                       # cod_assunto
    data_vigencia = models.DateField(blank=True, null=True)                                                                       # dat_vigencia
    timestamp = models.DateTimeField()                                                                                            # timestamp

    class Meta:
        verbose_name = _(u'Norma Jurídica')
        verbose_name_plural = _(u'Normas Jurídicas')


class LegislacaoCitada(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                                                # cod_materia
    norma = models.ForeignKey(NormaJuridica)                                                                       # cod_norma
    descricao_disposicoes = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Disposição'))  # des_disposicoes
    descricao_parte = models.CharField(max_length=8, blank=True, null=True, verbose_name=_(u'Parte'))              # des_parte
    descricao_livro = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Livro'))              # des_livro
    descricao_titulo = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Título'))            # des_titulo
    descricao_capitulo = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Capítulo'))        # des_capitulo
    descricao_secao = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Seção'))              # des_secao
    descricao_subsecao = models.CharField(max_length=7, blank=True, null=True, verbose_name=_(u'Subseção'))        # des_subsecao
    descricao_artigo = models.CharField(max_length=4, blank=True, null=True, verbose_name=_(u'Artigo'))            # des_artigo
    descricao_paragrafo = models.CharField(max_length=3, blank=True, null=True, verbose_name=_(u'Parágrafo'))      # des_paragrafo
    descricao_inciso = models.CharField(max_length=10, blank=True, null=True, verbose_name=_(u'Inciso'))           # des_inciso
    descricao_alinea = models.CharField(max_length=3, blank=True, null=True, verbose_name=_(u'Alínea'))            # des_alinea
    descricao_item = models.CharField(max_length=3, blank=True, null=True, verbose_name=_(u'Item'))                # des_item

    class Meta:
        verbose_name = _(u'Matéria Legislativa')
        verbose_name_plural = _(u'Matérias Legislativas')


class VinculoNormaJuridica(models.Model):
    # TODO M2M ???
    norma_referente = models.ForeignKey(NormaJuridica, related_name='+')  # cod_norma_referente
    norma_referida = models.ForeignKey(NormaJuridica, related_name='+')   # cod_norma_referida
    tipo_vinculo = models.CharField(max_length=1, blank=True, null=True)  # tip_vinculo

    class Meta:
        verbose_name = _(u'Vínculo entre Normas Jurídicas')
        verbose_name_plural = _(u'Vínculos entre Normas Jurídicas')
