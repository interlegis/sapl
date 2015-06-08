from django.db import models

from materia.models import MateriaLegislativa
from parlamentares.models import CargoMesa
from parlamentares.models import Parlamentar
from parlamentares.models import SessaoLegislativa


class ExpedienteMateria(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_materia = models.IntegerField()
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()


class ExpedienteSessaoPlenaria(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    expediente = models.ForeignKey(TipoExpediente)
    txt_expediente = models.TextField(blank=True, null=True)


class MesaSessaoPlenaria(models.Model):
    cargo = models.ForeignKey(CargoMesa)
    sessao_leg = models.ForeignKey(SessaoLegislativa)
    parlamentar = models.ForeignKey(Parlamentar)
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    ind_excluido = models.IntegerField(blank=True, null=True)


class Oradores(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    num_ordem = models.IntegerField()
    url_discurso = models.CharField(max_length=150, blank=True, null=True)


class OradoresExpediente(models.Model):
    cod_sessao_plen = models.IntegerField()
    parlamentar = models.ForeignKey(Parlamentar)
    num_ordem = models.IntegerField()
    url_discurso = models.CharField(max_length=150, blank=True, null=True)


class OrdemDia(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    materia = models.ForeignKey(MateriaLegislativa)
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()


class OrdemDiaPresenca(models.Model):
    cod_presenca_ordem_dia = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    parlamentar = models.ForeignKey(Parlamentar)
    dat_ordem = models.DateField()


class RegistroVotacao(models.Model):
    cod_votacao = models.AutoField(primary_key=True)
    tip_resultado_votacao = models.ForeignKey(TipoResultadoVotacao)
    materia = models.ForeignKey(MateriaLegislativa)
    ordem = models.ForeignKey(OrdemDia)
    num_votos_sim = models.IntegerField()
    num_votos_nao = models.IntegerField()
    num_abstencao = models.IntegerField()
    txt_observacao = models.TextField(blank=True, null=True)


class RegistroVotacaoParlamentar(models.Model):
    votacao = models.ForeignKey(RegistroVotacao)
    parlamentar = models.ForeignKey(Parlamentar)
    vot_parlamentar = models.CharField(max_length=10)


class SessaoPlenaria(models.Model):
    cod_sessao_plen = models.AutoField(primary_key=True)
    andamento_sessao = models.ForeignKey(AndamentoSessao, blank=True, null=True)
    tip_sessao = models.ForeignKey(TipoSessaoPlenaria)
    sessao_leg = models.ForeignKey(SessaoLegislativa)
    legislatura = models.ForeignKey(Legislatura)
    tip_expediente = models.CharField(max_length=10)
    dat_inicio_sessao = models.DateField()
    dia_sessao = models.CharField(max_length=15)
    hr_inicio_sessao = models.CharField(max_length=5)
    hr_fim_sessao = models.CharField(max_length=5, blank=True, null=True)
    num_sessao_plen = models.IntegerField()
    dat_fim_sessao = models.DateField(blank=True, null=True)
    url_audio = models.CharField(max_length=150, blank=True, null=True)
    url_video = models.CharField(max_length=150, blank=True, null=True)


class SessaoPlenariaPresenca(models.Model):
    cod_presenca_sessao = models.AutoField(primary_key=True)
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    dat_sessao = models.DateField(blank=True, null=True)


class TipoExpediente(models.Model):
    cod_expediente = models.AutoField(primary_key=True)
    nom_expediente = models.CharField(max_length=100)


class TipoResultadoVotacao(models.Model):
    tip_resultado_votacao = models.AutoField(primary_key=True)
    nom_resultado = models.CharField(max_length=100)


class TipoSessaoPlenaria(models.Model):
    tip_sessao = models.AutoField(primary_key=True)
    nom_sessao = models.CharField(max_length=30)
    num_minimo = models.IntegerField()
