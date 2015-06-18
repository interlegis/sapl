from django.db import models

from materia.models import MateriaLegislativa
from parlamentares.models import CargoMesa, Parlamentar, SessaoLegislativa, Legislatura


class TipoSessaoPlenaria(models.Model):
    nome_sessao = models.CharField(max_length=30)  # nom_sessao
    numero_minimo = models.IntegerField()          # num_minimo


class SessaoPlenaria(models.Model):
    # TODO lixo??? parece que era FK. Seria:
    # andamento_sessao = models.ForeignKey(AndamentoSessao, blank=True, null=True)
    cod_andamento_sessao = models.IntegerField(blank=True, null=True)      # cod_andamento_sessao

    tipo = models.ForeignKey(TipoSessaoPlenaria)                           # tip_sessao
    sessao_leg = models.ForeignKey(SessaoLegislativa)                      # cod_sessao_leg
    legislatura = models.ForeignKey(Legislatura)                           # num_legislatura
    tipo_expediente = models.CharField(max_length=10)                      # tip_expediente
    data_inicio_sessao = models.DateField()                                # dat_inicio_sessao
    dia_sessao = models.CharField(max_length=15)                           # dia_sessao
    hr_inicio_sessao = models.CharField(max_length=5)                      # hr_inicio_sessao
    hr_fim_sessao = models.CharField(max_length=5, blank=True, null=True)  # hr_fim_sessao
    numero_sessao_plen = models.IntegerField()                             # num_sessao_plen
    data_fim_sessao = models.DateField(blank=True, null=True)              # dat_fim_sessao
    url_audio = models.CharField(max_length=150, blank=True, null=True)    # url_audio
    url_video = models.CharField(max_length=150, blank=True, null=True)    # url_video


class ExpedienteMateria(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)           # cod_sessao_plen
    materia = models.ForeignKey(MateriaLegislativa)           # cod_materia
    data_ordem = models.DateField()                           # dat_ordem
    txt_observacao = models.TextField(blank=True, null=True)  # txt_observacao
    numero_ordem = models.IntegerField()                      # num_ordem
    txt_resultado = models.TextField(blank=True, null=True)   # txt_resultado
    tipo_votacao = models.IntegerField()                      # tip_votacao


class TipoExpediente(models.Model):
    nome_expediente = models.CharField(max_length=100)  # nom_expediente


class ExpedienteSessaoPlenaria(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)           # cod_sessao_plen
    expediente = models.ForeignKey(TipoExpediente)            # cod_expediente
    txt_expediente = models.TextField(blank=True, null=True)  # txt_expediente


class MesaSessaoPlenaria(models.Model):
    cargo = models.ForeignKey(CargoMesa)               # cod_cargo
    sessao_leg = models.ForeignKey(SessaoLegislativa)  # cod_sessao_leg
    parlamentar = models.ForeignKey(Parlamentar)       # cod_parlamentar
    sessao_plen = models.ForeignKey(SessaoPlenaria)    # cod_sessao_plen


class Oradores(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)                         # cod_sessao_plen
    parlamentar = models.ForeignKey(Parlamentar)                            # cod_parlamentar
    numero_ordem = models.IntegerField()                                    # num_ordem
    url_discurso = models.CharField(max_length=150, blank=True, null=True)  # url_discurso


class OradoresExpediente(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)                         # cod_sessao_plen
    parlamentar = models.ForeignKey(Parlamentar)                            # cod_parlamentar
    numero_ordem = models.IntegerField()                                    # num_ordem
    url_discurso = models.CharField(max_length=150, blank=True, null=True)  # url_discurso


class OrdemDia(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)           # cod_sessao_plen
    materia = models.ForeignKey(MateriaLegislativa)           # cod_materia
    data_ordem = models.DateField()                           # dat_ordem
    txt_observacao = models.TextField(blank=True, null=True)  # txt_observacao
    numero_ordem = models.IntegerField()                      # num_ordem
    txt_resultado = models.TextField(blank=True, null=True)   # txt_resultado
    tipo_votacao = models.IntegerField()                      # tip_votacao


class OrdemDiaPresenca(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)  # cod_sessao_plen
    parlamentar = models.ForeignKey(Parlamentar)     # cod_parlamentar
    data_ordem = models.DateField()                  # dat_ordem


class TipoResultadoVotacao(models.Model):
    nome_resultado = models.CharField(max_length=100)  # nom_resultado


class RegistroVotacao(models.Model):
    tipo_resultado_votacao = models.ForeignKey(TipoResultadoVotacao)  # tip_resultado_votacao
    materia = models.ForeignKey(MateriaLegislativa)                   # cod_materia
    ordem = models.ForeignKey(OrdemDia)                               # cod_ordem
    numero_votos_sim = models.IntegerField()                          # num_votos_sim
    numero_votos_nao = models.IntegerField()                          # num_votos_nao
    numero_abstencao = models.IntegerField()                          # num_abstencao
    txt_observacao = models.TextField(blank=True, null=True)          # txt_observacao


class RegistroVotacaoParlamentar(models.Model):
    votacao = models.ForeignKey(RegistroVotacao)       # cod_votacao
    parlamentar = models.ForeignKey(Parlamentar)       # cod_parlamentar
    vot_parlamentar = models.CharField(max_length=10)  # vot_parlamentar


class SessaoPlenariaPresenca(models.Model):
    sessao_plen = models.ForeignKey(SessaoPlenaria)        # cod_sessao_plen
    parlamentar = models.ForeignKey(Parlamentar)           # cod_parlamentar
    data_sessao = models.DateField(blank=True, null=True)  # dat_sessao
