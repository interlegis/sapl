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


class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura)
    nom_coligacao = models.CharField(max_length=50)
    num_votos_coligacao = models.IntegerField(blank=True, null=True)


class Partido(models.Model):
    sgl_partido = models.CharField(max_length=9)
    nom_partido = models.CharField(max_length=50)
    dat_criacao = models.DateField(blank=True, null=True)
    dat_extincao = models.DateField(blank=True, null=True)


class ComposicaoColigacao(models.Model):
    partido = models.ForeignKey(Partido)
    coligacao = models.ForeignKey(Coligacao)


class Localidade(models.Model):
    nom_localidade = models.CharField(max_length=50, blank=True, null=True)
    nom_localidade_pesq = models.CharField(max_length=50, blank=True, null=True)
    tip_localidade = models.CharField(max_length=1, blank=True, null=True)
    sgl_uf = models.CharField(max_length=2, blank=True, null=True)
    sgl_regiao = models.CharField(max_length=2, blank=True, null=True)


class NivelInstrucao(models.Model):
    nivel_instrucao = models.CharField(max_length=50)


class SituacaoMilitar(models.Model):
    des_tipo_situacao = models.CharField(max_length=50)


class Parlamentar(models.Model):
    nivel_instrucao = models.ForeignKey(NivelInstrucao, blank=True, null=True)
    situacao_militar = models.ForeignKey(SituacaoMilitar, blank=True, null=True)
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
    localidade_resid = models.ForeignKey(Localidade, blank=True, null=True)
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


class TipoDependente(models.Model):
    des_tipo_dependente = models.CharField(max_length=50)


class Dependente(models.Model):
    tipo_dependente = models.ForeignKey(TipoDependente)
    parlamentar = models.ForeignKey(Parlamentar)
    nom_dependente = models.CharField(max_length=50)
    sex_dependente = models.CharField(max_length=1)
    dat_nascimento = models.DateField(blank=True, null=True)
    num_cpf = models.CharField(max_length=14, blank=True, null=True)
    num_rg = models.CharField(max_length=15, blank=True, null=True)
    num_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)


class Filiacao(models.Model):
    dat_filiacao = models.DateField()
    parlamentar = models.ForeignKey(Parlamentar)
    partido = models.ForeignKey(Partido)
    dat_desfiliacao = models.DateField(blank=True, null=True)


class TipoAfastamento(models.Model):
    des_afastamento = models.CharField(max_length=50)
    ind_afastamento = models.IntegerField()
    ind_fim_mandato = models.IntegerField()
    des_dispositivo = models.CharField(max_length=50, blank=True, null=True)


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    tipo_afastamento = models.ForeignKey(TipoAfastamento, blank=True, null=True)
    legislatura = models.ForeignKey(Legislatura)
    coligacao = models.ForeignKey(Coligacao, blank=True, null=True)
    tip_causa_fim_mandato = models.IntegerField(blank=True, null=True)
    dat_fim_mandato = models.DateField(blank=True, null=True)
    num_votos_recebidos = models.IntegerField(blank=True, null=True)
    dat_expedicao_diploma = models.DateField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)


class CargoMesa(models.Model):
    nome = models.CharField(max_length=50)
    unico = models.BooleanField()


class ComposicaoMesa(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa)
    cargo = models.ForeignKey(CargoMesa)
