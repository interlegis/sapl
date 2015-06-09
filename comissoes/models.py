from django.db import models

from parlamentares.models import Parlamentar


class TipoComissao(models.Model):
    nome_tipo_comissao = models.CharField(max_length=50)
    sigla_natureza_comissao = models.CharField(max_length=1)
    sigla_tipo_comissao = models.CharField(max_length=10)
    descricao_dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True)


class Comissao(models.Model):
    tipo_comissao = models.ForeignKey(TipoComissao)
    nome_comissao = models.CharField(max_length=60)
    sigla_comissao = models.CharField(max_length=10)
    data_criacao = models.DateField()
    data_extincao = models.DateField(blank=True, null=True)
    nome_apelido_temp = models.CharField(max_length=100, blank=True, null=True)
    data_instalacao_temp = models.DateField(blank=True, null=True)
    data_final_prevista_temp = models.DateField(blank=True, null=True)
    data_prorrogada_temp = models.DateField(blank=True, null=True)
    data_fim_comissao = models.DateField(blank=True, null=True)
    nome_secretario = models.CharField(max_length=30, blank=True, null=True)
    numero_tel_reuniao = models.CharField(max_length=15, blank=True, null=True)
    endereco_secretaria = models.CharField(max_length=100, blank=True, null=True)
    numero_tel_secretaria = models.CharField(max_length=15, blank=True, null=True)
    numero_fax_secretaria = models.CharField(max_length=15, blank=True, null=True)
    descricao_agenda_reuniao = models.CharField(max_length=100, blank=True, null=True)
    local_reuniao = models.CharField(max_length=100, blank=True, null=True)
    txt_finalidade = models.TextField(blank=True, null=True)
    endereco_email = models.CharField(max_length=100, blank=True, null=True)
    unid_deliberativa = models.BooleanField()


class PeriodoCompComissao(models.Model):
    data_inicio_periodo = models.DateField()
    data_fim_periodo = models.DateField(blank=True, null=True)


class CargoComissao(models.Model):
    nome = models.CharField(max_length=50)
    unico = models.BooleanField()


class ComposicaoComissao(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    comissao = models.ForeignKey(Comissao)
    periodo_comp = models.ForeignKey(PeriodoCompComissao)
    cargo = models.ForeignKey(CargoComissao)
    titular = models.BooleanField()
    data_designacao = models.DateField()
    data_desligamento = models.DateField(blank=True, null=True)
    descricao_motivo_desligamento = models.CharField(max_length=150, blank=True, null=True)
    obs_composicao = models.CharField(max_length=150, blank=True, null=True)
