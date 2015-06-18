from django.db import models

from parlamentares.models import Parlamentar


class TipoComissao(models.Model):
    nome_tipo_comissao = models.CharField(max_length=50)                                       # nom_tipo_comissao
    sigla_natureza_comissao = models.CharField(max_length=1)                                   # sgl_natureza_comissao
    sigla_tipo_comissao = models.CharField(max_length=10)                                      # sgl_tipo_comissao
    descricao_dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True)  # des_dispositivo_regimental


class Comissao(models.Model):
    tipo_comissao = models.ForeignKey(TipoComissao)                                     # tip_comissao
    nome_comissao = models.CharField(max_length=60)                                     # nom_comissao
    sigla_comissao = models.CharField(max_length=10)                                    # sgl_comissao
    data_criacao = models.DateField()                                                   # dat_criacao
    data_extincao = models.DateField(blank=True, null=True)                             # dat_extincao
    nome_apelido_temp = models.CharField(max_length=100, blank=True, null=True)         # nom_apelido_temp
    data_instalacao_temp = models.DateField(blank=True, null=True)                      # dat_instalacao_temp
    data_final_prevista_temp = models.DateField(blank=True, null=True)                  # dat_final_prevista_temp
    data_prorrogada_temp = models.DateField(blank=True, null=True)                      # dat_prorrogada_temp
    data_fim_comissao = models.DateField(blank=True, null=True)                         # dat_fim_comissao
    nome_secretario = models.CharField(max_length=30, blank=True, null=True)            # nom_secretario
    numero_tel_reuniao = models.CharField(max_length=15, blank=True, null=True)         # num_tel_reuniao
    endereco_secretaria = models.CharField(max_length=100, blank=True, null=True)       # end_secretaria
    numero_tel_secretaria = models.CharField(max_length=15, blank=True, null=True)      # num_tel_secretaria
    numero_fax_secretaria = models.CharField(max_length=15, blank=True, null=True)      # num_fax_secretaria
    descricao_agenda_reuniao = models.CharField(max_length=100, blank=True, null=True)  # des_agenda_reuniao
    local_reuniao = models.CharField(max_length=100, blank=True, null=True)             # loc_reuniao
    txt_finalidade = models.TextField(blank=True, null=True)                            # txt_finalidade
    endereco_email = models.CharField(max_length=100, blank=True, null=True)            # end_email
    unid_deliberativa = models.BooleanField()                                           # ind_unid_deliberativa


class PeriodoCompComissao(models.Model):
    data_inicio_periodo = models.DateField()                    # dat_inicio_periodo
    data_fim_periodo = models.DateField(blank=True, null=True)  # dat_fim_periodo


class CargoComissao(models.Model):
    nome = models.CharField(max_length=50)  # des_cargo
    unico = models.BooleanField()           # ind_unico


class ComposicaoComissao(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)                                             # cod_parlamentar
    comissao = models.ForeignKey(Comissao)                                                   # cod_comissao
    periodo_comp = models.ForeignKey(PeriodoCompComissao)                                    # cod_periodo_comp
    cargo = models.ForeignKey(CargoComissao)                                                 # cod_cargo
    titular = models.BooleanField()                                                          # ind_titular
    data_designacao = models.DateField()                                                     # dat_designacao
    data_desligamento = models.DateField(blank=True, null=True)                              # dat_desligamento
    descricao_motivo_desligamento = models.CharField(max_length=150, blank=True, null=True)  # des_motivo_desligamento
    obs_composicao = models.CharField(max_length=150, blank=True, null=True)                 # obs_composicao
