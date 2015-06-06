from django.db import models


class Coligacao(models.Model):
    cod_coligacao = models.AutoField(primary_key=True)
    num_legislatura = models.IntegerField()
    nom_coligacao = models.CharField(max_length=50)
    num_votos_coligacao = models.IntegerField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class ComposicaoColigacao(models.Model):
    cod_partido = models.IntegerField()
    cod_coligacao = models.IntegerField()
    ind_excluido = models.IntegerField()


class Dependente(models.Model):
    cod_dependente = models.AutoField(primary_key=True)
    tip_dependente = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    nom_dependente = models.CharField(max_length=50)
    sex_dependente = models.CharField(max_length=1)
    dat_nascimento = models.DateField(blank=True, null=True)
    num_cpf = models.CharField(max_length=14, blank=True, null=True)
    num_rg = models.CharField(max_length=15, blank=True, null=True)
    num_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)
    ind_excluido = models.IntegerField()


class Filiacao(models.Model):
    dat_filiacao = models.DateField()
    cod_parlamentar = models.IntegerField()
    cod_partido = models.IntegerField()
    dat_desfiliacao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class Localidade(models.Model):
    cod_localidade = models.IntegerField(primary_key=True)
    nom_localidade = models.CharField(max_length=50, blank=True, null=True)
    nom_localidade_pesq = models.CharField(max_length=50, blank=True, null=True)
    tip_localidade = models.CharField(max_length=1, blank=True, null=True)
    sgl_uf = models.CharField(max_length=2, blank=True, null=True)
    sgl_regiao = models.CharField(max_length=2, blank=True, null=True)
    ind_excluido = models.IntegerField()


class Mandato(models.Model):
    cod_mandato = models.AutoField(primary_key=True)
    cod_parlamentar = models.IntegerField()
    tip_afastamento = models.IntegerField(blank=True, null=True)
    num_legislatura = models.IntegerField()
    cod_coligacao = models.IntegerField(blank=True, null=True)
    tip_causa_fim_mandato = models.IntegerField(blank=True, null=True)
    dat_fim_mandato = models.DateField(blank=True, null=True)
    num_votos_recebidos = models.IntegerField(blank=True, null=True)
    dat_expedicao_diploma = models.DateField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class NivelInstrucao(models.Model):
    nivel_instrucao = models.CharField(max_length=50)


class Parlamentar(models.Model):
    cod_parlamentar = models.AutoField(primary_key=True)
    cod_nivel_instrucao = models.IntegerField(blank=True, null=True)
    tip_situacao_militar = models.IntegerField(blank=True, null=True)
    nom_completo = models.CharField(max_length=50)
    nom_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    sex_parlamentar = models.CharField(max_length=1)
    dat_nascimento = models.DateField(blank=True, null=True)
    num_cpf = models.CharField(max_length=14, blank=True, null=True)
    num_rg = models.CharField(max_length=15, blank=True, null=True)
    num_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)
    cod_casa = models.IntegerField()
    num_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True)
    num_tel_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    num_fax_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    end_residencial = models.CharField(max_length=100, blank=True, null=True)
    cod_localidade_resid = models.IntegerField(blank=True, null=True)
    num_cep_resid = models.CharField(max_length=9, blank=True, null=True)
    num_tel_resid = models.CharField(max_length=50, blank=True, null=True)
    num_fax_resid = models.CharField(max_length=50, blank=True, null=True)
    end_web = models.CharField(max_length=100, blank=True, null=True)
    nom_profissao = models.CharField(max_length=50, blank=True, null=True)
    end_email = models.CharField(max_length=100, blank=True, null=True)
    des_local_atuacao = models.CharField(max_length=100, blank=True, null=True)
    ind_ativo = models.IntegerField()
    txt_biografia = models.TextField(blank=True, null=True)
    ind_unid_deliberativa = models.IntegerField()
    ind_excluido = models.IntegerField()


class Partido(models.Model):
    cod_partido = models.AutoField(primary_key=True)
    sgl_partido = models.CharField(max_length=9)
    nom_partido = models.CharField(max_length=50)
    dat_criacao = models.DateField(blank=True, null=True)
    dat_extincao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class TipoAfastamento(models.Model):
    tip_afastamento = models.AutoField(primary_key=True)
    des_afastamento = models.CharField(max_length=50)
    ind_afastamento = models.IntegerField()
    ind_fim_mandato = models.IntegerField()
    des_dispositivo = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.IntegerField()


class TipoDependente(models.Model):
    tip_dependente = models.AutoField(primary_key=True)
    des_tipo_dependente = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class TipoSituacaoMilitar(models.Model):
    tip_situacao_militar = models.IntegerField(primary_key=True)
    des_tipo_situacao = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


