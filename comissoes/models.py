from django.db import models

from parlamentares.models import Parlamentar


class TipoComissao(models.Model):
    tip_comissao = models.AutoField(primary_key=True)
    nom_tipo_comissao = models.CharField(max_length=50)
    sgl_natureza_comissao = models.CharField(max_length=1)
    sgl_tipo_comissao = models.CharField(max_length=10)
    des_dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True)


class Comissao(models.Model):
    cod_comissao = models.AutoField(primary_key=True)
    tip_comissao = models.ForeignKey(TipoComissao)
    nom_comissao = models.CharField(max_length=60)
    sgl_comissao = models.CharField(max_length=10)
    dat_criacao = models.DateField()
    dat_extincao = models.DateField(blank=True, null=True)
    nom_apelido_temp = models.CharField(max_length=100, blank=True, null=True)
    dat_instalacao_temp = models.DateField(blank=True, null=True)
    dat_final_prevista_temp = models.DateField(blank=True, null=True)
    dat_prorrogada_temp = models.DateField(blank=True, null=True)
    dat_fim_comissao = models.DateField(blank=True, null=True)
    nom_secretario = models.CharField(max_length=30, blank=True, null=True)
    num_tel_reuniao = models.CharField(max_length=15, blank=True, null=True)
    end_secretaria = models.CharField(max_length=100, blank=True, null=True)
    num_tel_secretaria = models.CharField(max_length=15, blank=True, null=True)
    num_fax_secretaria = models.CharField(max_length=15, blank=True, null=True)
    des_agenda_reuniao = models.CharField(max_length=100, blank=True, null=True)
    loc_reuniao = models.CharField(max_length=100, blank=True, null=True)
    txt_finalidade = models.TextField(blank=True, null=True)
    end_email = models.CharField(max_length=100, blank=True, null=True)
    ind_unid_deliberativa = models.IntegerField()


class PeriodoCompComissao(models.Model):
    cod_periodo_comp = models.AutoField(primary_key=True)
    dat_inicio_periodo = models.DateField()
    dat_fim_periodo = models.DateField(blank=True, null=True)


class CargoComissao(models.Model):
    ###
    nome = models.CharField(max_length=50)
    ind_unico = models.IntegerField()


class ComposicaoComissao(models.Model):
    cod_comp_comissao = models.AutoField(primary_key=True)
    parlamentar = models.ForeignKey(Parlamentar)
    comissao = models.ForeignKey(Comissao)
    periodo_comp = models.ForeignKey(PeriodoCompComissao)
    cargo = models.ForeignKey(CargoComissao)
    ind_titular = models.IntegerField()
    dat_designacao = models.DateField()
    dat_desligamento = models.DateField(blank=True, null=True)
    des_motivo_desligamento = models.CharField(max_length=150, blank=True, null=True)
    obs_composicao = models.CharField(max_length=150, blank=True, null=True)
