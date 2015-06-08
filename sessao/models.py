from django.db import models

from materia.models import MateriaLegislativa
from parlamentares.models import CargoMesa, Parlamentar, SessaoLegislativa, Legislatura


class TipoSessaoPlenaria(models.Model):
    nom_sessao = models.CharField(max_length=30)
    num_minimo = models.IntegerField()


class SessaoPlenaria(models.Model):
    cod_andamento_sessao = models.IntegerField(blank=True, null=True)  # TODO lixo??? parece que era FK
    # andamento_sessao = models.ForeignKey(AndamentoSessao, blank=True, null=True)
    tipo = models.ForeignKey(TipoSessaoPlenaria)
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


class ExpedienteMateria(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    materia = models.ForeignKey(MateriaLegislativa)
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()


class TipoExpediente(models.Model):
    nom_expediente = models.CharField(max_length=100)


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
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    num_ordem = models.IntegerField()
    url_discurso = models.CharField(max_length=150, blank=True, null=True)


class OrdemDia(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    materia = models.ForeignKey(MateriaLegislativa)
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()


class OrdemDiaPresenca(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    dat_ordem = models.DateField()


class TipoResultadoVotacao(models.Model):
    nom_resultado = models.CharField(max_length=100)


class RegistroVotacao(models.Model):
    tipo_resultado_votacao = models.ForeignKey(TipoResultadoVotacao)
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


class SessaoPlenariaPresenca(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)
    parlamentar = models.ForeignKey(Parlamentar)
    dat_sessao = models.DateField(blank=True, null=True)
