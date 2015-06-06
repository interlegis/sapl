from django.db import models


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


class NivelInstrucao(models.Model):
    nivel_instrucao = models.CharField(max_length=50)
