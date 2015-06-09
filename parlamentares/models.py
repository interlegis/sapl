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
    nome_coligacao = models.CharField(max_length=50)
    numero_votos_coligacao = models.IntegerField(blank=True, null=True)


class Partido(models.Model):
    sigla_partido = models.CharField(max_length=9)
    nome_partido = models.CharField(max_length=50)
    data_criacao = models.DateField(blank=True, null=True)
    data_extincao = models.DateField(blank=True, null=True)


class ComposicaoColigacao(models.Model):
    partido = models.ForeignKey(Partido)
    coligacao = models.ForeignKey(Coligacao)


class Localidade(models.Model):
    nome_localidade = models.CharField(max_length=50, blank=True, null=True)
    nome_localidade_pesq = models.CharField(max_length=50, blank=True, null=True)
    tipo_localidade = models.CharField(max_length=1, blank=True, null=True)
    sigla_uf = models.CharField(max_length=2, blank=True, null=True)
    sigla_regiao = models.CharField(max_length=2, blank=True, null=True)


class NivelInstrucao(models.Model):
    nivel_instrucao = models.CharField(max_length=50)


class SituacaoMilitar(models.Model):
    descricao_tipo_situacao = models.CharField(max_length=50)


class Parlamentar(models.Model):
    nivel_instrucao = models.ForeignKey(NivelInstrucao, blank=True, null=True)
    situacao_militar = models.ForeignKey(SituacaoMilitar, blank=True, null=True)
    nome_completo = models.CharField(max_length=50)
    nome_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    sexo = models.CharField(max_length=1)
    data_nascimento = models.DateField(blank=True, null=True)
    numero_cpf = models.CharField(max_length=14, blank=True, null=True)
    numero_rg = models.CharField(max_length=15, blank=True, null=True)
    numero_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)
    cod_casa = models.IntegerField()
    numero_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True)
    numero_tel_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    numero_fax_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    endereco_residencial = models.CharField(max_length=100, blank=True, null=True)
    localidade_resid = models.ForeignKey(Localidade, blank=True, null=True)
    numero_cep_resid = models.CharField(max_length=9, blank=True, null=True)
    numero_tel_resid = models.CharField(max_length=50, blank=True, null=True)
    numero_fax_resid = models.CharField(max_length=50, blank=True, null=True)
    endereco_web = models.CharField(max_length=100, blank=True, null=True)
    nome_profissao = models.CharField(max_length=50, blank=True, null=True)
    endereco_email = models.CharField(max_length=100, blank=True, null=True)
    descricao_local_atuacao = models.CharField(max_length=100, blank=True, null=True)
    ativo = models.BooleanField()
    txt_biografia = models.TextField(blank=True, null=True)
    unid_deliberativa = models.BooleanField()


class TipoDependente(models.Model):
    descricao_tipo_dependente = models.CharField(max_length=50)


class Dependente(models.Model):
    tipo_dependente = models.ForeignKey(TipoDependente)
    parlamentar = models.ForeignKey(Parlamentar)
    nome_dependente = models.CharField(max_length=50)
    sexo = models.CharField(max_length=1)
    data_nascimento = models.DateField(blank=True, null=True)
    numero_cpf = models.CharField(max_length=14, blank=True, null=True)
    numero_rg = models.CharField(max_length=15, blank=True, null=True)
    numero_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)


class Filiacao(models.Model):
    data_filiacao = models.DateField()
    parlamentar = models.ForeignKey(Parlamentar)
    partido = models.ForeignKey(Partido)
    data_desfiliacao = models.DateField(blank=True, null=True)


class TipoAfastamento(models.Model):
    descricao_afastamento = models.CharField(max_length=50)
    afastamento = models.BooleanField()
    fim_mandato = models.BooleanField()
    descricao_dispositivo = models.CharField(max_length=50, blank=True, null=True)


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    tipo_afastamento = models.ForeignKey(TipoAfastamento, blank=True, null=True)
    legislatura = models.ForeignKey(Legislatura)
    coligacao = models.ForeignKey(Coligacao, blank=True, null=True)
    tipo_causa_fim_mandato = models.IntegerField(blank=True, null=True)
    data_fim_mandato = models.DateField(blank=True, null=True)
    numero_votos_recebidos = models.IntegerField(blank=True, null=True)
    data_expedicao_diploma = models.DateField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)


class CargoMesa(models.Model):
    nome = models.CharField(max_length=50)
    unico = models.BooleanField()


class ComposicaoMesa(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa)
    cargo = models.ForeignKey(CargoMesa)
