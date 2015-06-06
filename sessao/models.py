from django.db import models


class ExpedienteMateria(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_materia = models.IntegerField()
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()


class ExpedienteSessaoPlenaria(models.Model):
    cod_sessao_plen = models.IntegerField()
    cod_expediente = models.IntegerField()
    txt_expediente = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class MesaSessaoPlenaria(models.Model):
    cod_cargo = models.IntegerField()
    cod_sessao_leg = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    cod_sessao_plen = models.IntegerField()
    ind_excluido = models.IntegerField(blank=True, null=True)


class Oradores(models.Model):
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    num_ordem = models.IntegerField()
    url_discurso = models.CharField(max_length=150, blank=True, null=True)
    ind_excluido = models.IntegerField()


class OradoresExpediente(models.Model):
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    num_ordem = models.IntegerField()
    url_discurso = models.CharField(max_length=150, blank=True, null=True)
    ind_excluido = models.IntegerField()


class OrdemDia(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_materia = models.IntegerField()
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()


class OrdemDiaPresenca(models.Model):
    cod_presenca_ordem_dia = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    dat_ordem = models.DateField()
    ind_excluido = models.IntegerField()


class RegistroVotacao(models.Model):
    cod_votacao = models.AutoField(primary_key=True)
    tip_resultado_votacao = models.IntegerField()
    cod_materia = models.IntegerField()
    cod_ordem = models.IntegerField()
    num_votos_sim = models.IntegerField()
    num_votos_nao = models.IntegerField()
    num_abstencao = models.IntegerField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class RegistroVotacaoParlamentar(models.Model):
    cod_votacao = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    ind_excluido = models.IntegerField()
    vot_parlamentar = models.CharField(max_length=10)


class SessaoPlenaria(models.Model):
    cod_sessao_plen = models.AutoField(primary_key=True)
    cod_andamento_sessao = models.IntegerField(blank=True, null=True)
    tip_sessao = models.IntegerField()
    cod_sessao_leg = models.IntegerField()
    num_legislatura = models.IntegerField()
    tip_expediente = models.CharField(max_length=10)
    dat_inicio_sessao = models.DateField()
    dia_sessao = models.CharField(max_length=15)
    hr_inicio_sessao = models.CharField(max_length=5)
    hr_fim_sessao = models.CharField(max_length=5, blank=True, null=True)
    num_sessao_plen = models.IntegerField()
    dat_fim_sessao = models.DateField(blank=True, null=True)
    url_audio = models.CharField(max_length=150, blank=True, null=True)
    url_video = models.CharField(max_length=150, blank=True, null=True)
    ind_excluido = models.IntegerField()


class SessaoPlenariaPresenca(models.Model):
    cod_presenca_sessao = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    dat_sessao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class TipoExpediente(models.Model):
    cod_expediente = models.AutoField(primary_key=True)
    nom_expediente = models.CharField(max_length=100)
    ind_excluido = models.IntegerField()


class TipoResultadoVotacao(models.Model):
    tip_resultado_votacao = models.AutoField(primary_key=True)
    nom_resultado = models.CharField(max_length=100)
    ind_excluido = models.IntegerField()


class TipoSessaoPlenaria(models.Model):
    tip_sessao = models.AutoField(primary_key=True)
    nom_sessao = models.CharField(max_length=30)
    ind_excluido = models.IntegerField()
    num_minimo = models.IntegerField()
