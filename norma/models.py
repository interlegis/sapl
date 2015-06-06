from django.db import models


class AssuntoNorma(models.Model):
    cod_assunto = models.AutoField(primary_key=True)
    des_assunto = models.CharField(max_length=50)
    des_estendida = models.CharField(max_length=250, blank=True, null=True)
    ind_excluido = models.IntegerField()


class NormaJuridica(models.Model):
    cod_norma = models.AutoField(primary_key=True)
    tip_norma = models.IntegerField()
    cod_materia = models.IntegerField(blank=True, null=True)
    num_norma = models.IntegerField()
    ano_norma = models.SmallIntegerField()
    tip_esfera_federacao = models.CharField(max_length=1)
    dat_norma = models.DateField(blank=True, null=True)
    dat_publicacao = models.DateField(blank=True, null=True)
    des_veiculo_publicacao = models.CharField(max_length=30, blank=True, null=True)
    num_pag_inicio_publ = models.IntegerField(blank=True, null=True)
    num_pag_fim_publ = models.IntegerField(blank=True, null=True)
    txt_ementa = models.TextField()
    txt_indexacao = models.TextField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_complemento = models.IntegerField(blank=True, null=True)
    cod_assunto = models.CharField(max_length=16)
    dat_vigencia = models.DateField(blank=True, null=True)
    timestamp = models.DateTimeField()
    ind_excluido = models.IntegerField()


class TipoNormaJuridica(models.Model):
    tip_norma = models.AutoField(primary_key=True)
    voc_lexml = models.CharField(max_length=50, blank=True, null=True)
    sgl_tipo_norma = models.CharField(max_length=3)
    des_tipo_norma = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class VinculoNormaJuridica(models.Model):
    cod_vinculo = models.AutoField(primary_key=True)
    cod_norma_referente = models.IntegerField()
    cod_norma_referida = models.IntegerField()
    tip_vinculo = models.CharField(max_length=1, blank=True, null=True)
    ind_excluido = models.CharField(max_length=1)
