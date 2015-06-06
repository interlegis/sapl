from django.db import models


class CargoMesa(models.Model):
    cod_cargo = models.AutoField(primary_key=True)
    des_cargo = models.CharField(max_length=50)
    ind_unico = models.IntegerField()
    ind_excluido = models.IntegerField()


class ComposicaoMesa(models.Model):
    cod_parlamentar = models.IntegerField()
    cod_sessao_leg = models.IntegerField()
    cod_cargo = models.IntegerField()
    ind_excluido = models.IntegerField()


class Legislatura(models.Model):
    data_inicio = models.DateField()
    data_fim = models.DateField()
    data_eleicao = models.DateField()


class SessaoLegislativa(models.Model):
    legislatura = models.ForeignKey(Legislatura)
    numero = models.IntegerField()
    tipo = models.CharField(max_length=1)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    data_inicio_intervalo = models.DateField(blank=True, null=True)
    data_fim_intervalo = models.DateField(blank=True, null=True)
