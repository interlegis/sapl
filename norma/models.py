from django.db import models

from materia.models import MateriaLegislativa


class AssuntoNorma(models.Model):
    descricao_assunto = models.CharField(max_length=50)                            # des_assunto
    descricao_estendida = models.CharField(max_length=250, blank=True, null=True)  # des_estendida


class TipoNormaJuridica(models.Model):
    voc_lexml = models.CharField(max_length=50, blank=True, null=True)  # voc_lexml
    sigla_tipo_norma = models.CharField(max_length=3)                   # sgl_tipo_norma
    descricao_tipo_norma = models.CharField(max_length=50)              # des_tipo_norma


class NormaJuridica(models.Model):
    tipo = models.ForeignKey(TipoNormaJuridica)                                              # tip_norma
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)                   # cod_materia
    numero_norma = models.IntegerField()                                                     # num_norma
    ano_norma = models.SmallIntegerField()                                                   # ano_norma
    tipo_esfera_federacao = models.CharField(max_length=1)                                   # tip_esfera_federacao
    data_norma = models.DateField(blank=True, null=True)                                     # dat_norma
    data_publicacao = models.DateField(blank=True, null=True)                                # dat_publicacao
    descricao_veiculo_publicacao = models.CharField(max_length=30, blank=True, null=True)    # des_veiculo_publicacao
    numero_pag_inicio_publ = models.IntegerField(blank=True, null=True)                      # num_pag_inicio_publ
    numero_pag_fim_publ = models.IntegerField(blank=True, null=True)                         # num_pag_fim_publ
    txt_ementa = models.TextField()                                                          # txt_ementa
    txt_indexacao = models.TextField(blank=True, null=True)                                  # txt_indexacao
    txt_observacao = models.TextField(blank=True, null=True)                                 # txt_observacao
    complemento = models.NullBooleanField(blank=True)                                        # ind_complemento
    assunto = models.ForeignKey(AssuntoNorma)  # XXX was a CharField (attention on migrate)  # cod_assunto
    data_vigencia = models.DateField(blank=True, null=True)                                  # dat_vigencia
    timestamp = models.DateTimeField()                                                       # timestamp


# XXX maybe should be in materia app, but would cause a circular import
class LegislacaoCitada(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                 # cod_materia
    norma = models.ForeignKey(NormaJuridica)                                        # cod_norma
    descricao_disposicoes = models.CharField(max_length=15, blank=True, null=True)  # des_disposicoes
    descricao_parte = models.CharField(max_length=8, blank=True, null=True)         # des_parte
    descricao_livro = models.CharField(max_length=7, blank=True, null=True)         # des_livro
    descricao_titulo = models.CharField(max_length=7, blank=True, null=True)        # des_titulo
    descricao_capitulo = models.CharField(max_length=7, blank=True, null=True)      # des_capitulo
    descricao_secao = models.CharField(max_length=7, blank=True, null=True)         # des_secao
    descricao_subsecao = models.CharField(max_length=7, blank=True, null=True)      # des_subsecao
    descricao_artigo = models.CharField(max_length=4, blank=True, null=True)        # des_artigo
    descricao_paragrafo = models.CharField(max_length=3, blank=True, null=True)     # des_paragrafo
    descricao_inciso = models.CharField(max_length=10, blank=True, null=True)       # des_inciso
    descricao_alinea = models.CharField(max_length=3, blank=True, null=True)        # des_alinea
    descricao_item = models.CharField(max_length=3, blank=True, null=True)          # des_item


class VinculoNormaJuridica(models.Model):
    norma_referente = models.ForeignKey(NormaJuridica, related_name='+')  # cod_norma_referente
    norma_referida = models.ForeignKey(NormaJuridica, related_name='+')   # cod_norma_referida
    tipo_vinculo = models.CharField(max_length=1, blank=True, null=True)  # tip_vinculo
