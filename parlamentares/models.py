from django.db import models


class Legislatura(models.Model):
    data_inicio = models.DateField()   # dat_inicio
    data_fim = models.DateField()      # dat_fim
    data_eleicao = models.DateField()  # dat_eleicao


class SessaoLegislativa(models.Model):
    legislatura = models.ForeignKey(Legislatura)                     # num_legislatura
    numero = models.IntegerField()                                   # num_sessao_leg
    tipo = models.CharField(max_length=1)                            # tip_sessao_leg
    data_inicio = models.DateField()                                 # dat_inicio
    data_fim = models.DateField()                                    # dat_fim
    data_inicio_intervalo = models.DateField(blank=True, null=True)  # dat_inicio_intervalo
    data_fim_intervalo = models.DateField(blank=True, null=True)     # dat_fim_intervalo


class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura)                         # num_legislatura
    nome_coligacao = models.CharField(max_length=50)                     # nom_coligacao
    numero_votos_coligacao = models.IntegerField(blank=True, null=True)  # num_votos_coligacao


class Partido(models.Model):
    sigla_partido = models.CharField(max_length=9)           # sgl_partido
    nome_partido = models.CharField(max_length=50)           # nom_partido
    data_criacao = models.DateField(blank=True, null=True)   # dat_criacao
    data_extincao = models.DateField(blank=True, null=True)  # dat_extincao


class ComposicaoColigacao(models.Model):
    partido = models.ForeignKey(Partido)      # cod_partido
    coligacao = models.ForeignKey(Coligacao)  # cod_coligacao


class Localidade(models.Model):
    nome_localidade = models.CharField(max_length=50, blank=True, null=True)       # nom_localidade
    nome_localidade_pesq = models.CharField(max_length=50, blank=True, null=True)  # nom_localidade_pesq
    tipo_localidade = models.CharField(max_length=1, blank=True, null=True)        # tip_localidade
    sigla_uf = models.CharField(max_length=2, blank=True, null=True)               # sgl_uf
    sigla_regiao = models.CharField(max_length=2, blank=True, null=True)           # sgl_regiao


class NivelInstrucao(models.Model):
    nivel_instrucao = models.CharField(max_length=50)  # des_nivel_instrucao


class SituacaoMilitar(models.Model):
    descricao_tipo_situacao = models.CharField(max_length=50)  # des_tipo_situacao


class Parlamentar(models.Model):
    nivel_instrucao = models.ForeignKey(NivelInstrucao, blank=True, null=True)         # cod_nivel_instrucao
    situacao_militar = models.ForeignKey(SituacaoMilitar, blank=True, null=True)       # tip_situacao_militar
    nome_completo = models.CharField(max_length=50)                                    # nom_completo
    nome_parlamentar = models.CharField(max_length=50, blank=True, null=True)          # nom_parlamentar
    sexo = models.CharField(max_length=1)                                              # sex_parlamentar
    data_nascimento = models.DateField(blank=True, null=True)                          # dat_nascimento
    numero_cpf = models.CharField(max_length=14, blank=True, null=True)                # num_cpf
    numero_rg = models.CharField(max_length=15, blank=True, null=True)                 # num_rg
    numero_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)        # num_tit_eleitor
    cod_casa = models.IntegerField()                                                   # cod_casa
    numero_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True)    # num_gab_parlamentar
    numero_tel_parlamentar = models.CharField(max_length=50, blank=True, null=True)    # num_tel_parlamentar
    numero_fax_parlamentar = models.CharField(max_length=50, blank=True, null=True)    # num_fax_parlamentar
    endereco_residencial = models.CharField(max_length=100, blank=True, null=True)     # end_residencial
    localidade_resid = models.ForeignKey(Localidade, blank=True, null=True)            # cod_localidade_resid
    numero_cep_resid = models.CharField(max_length=9, blank=True, null=True)           # num_cep_resid
    numero_tel_resid = models.CharField(max_length=50, blank=True, null=True)          # num_tel_resid
    numero_fax_resid = models.CharField(max_length=50, blank=True, null=True)          # num_fax_resid
    endereco_web = models.CharField(max_length=100, blank=True, null=True)             # end_web
    nome_profissao = models.CharField(max_length=50, blank=True, null=True)            # nom_profissao
    endereco_email = models.CharField(max_length=100, blank=True, null=True)           # end_email
    descricao_local_atuacao = models.CharField(max_length=100, blank=True, null=True)  # des_local_atuacao
    ativo = models.BooleanField()                                                      # ind_ativo
    txt_biografia = models.TextField(blank=True, null=True)                            # txt_biografia
    unid_deliberativa = models.BooleanField()                                          # ind_unid_deliberativa


class TipoDependente(models.Model):
    descricao_tipo_dependente = models.CharField(max_length=50)  # des_tipo_dependente


class Dependente(models.Model):
    tipo_dependente = models.ForeignKey(TipoDependente)                          # tip_dependente
    parlamentar = models.ForeignKey(Parlamentar)                                 # cod_parlamentar
    nome_dependente = models.CharField(max_length=50)                            # nom_dependente
    sexo = models.CharField(max_length=1)                                        # sex_dependente
    data_nascimento = models.DateField(blank=True, null=True)                    # dat_nascimento
    numero_cpf = models.CharField(max_length=14, blank=True, null=True)          # num_cpf
    numero_rg = models.CharField(max_length=15, blank=True, null=True)           # num_rg
    numero_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)  # num_tit_eleitor


class Filiacao(models.Model):
    data_filiacao = models.DateField()                          # dat_filiacao
    parlamentar = models.ForeignKey(Parlamentar)                # cod_parlamentar
    partido = models.ForeignKey(Partido)                        # cod_partido
    data_desfiliacao = models.DateField(blank=True, null=True)  # dat_desfiliacao


class TipoAfastamento(models.Model):
    descricao_afastamento = models.CharField(max_length=50)                         # des_afastamento
    afastamento = models.BooleanField()                                             # ind_afastamento
    fim_mandato = models.BooleanField()                                             # ind_fim_mandato
    descricao_dispositivo = models.CharField(max_length=50, blank=True, null=True)  # des_dispositivo


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)                                  # cod_parlamentar
    tipo_afastamento = models.ForeignKey(TipoAfastamento, blank=True, null=True)  # tip_afastamento
    legislatura = models.ForeignKey(Legislatura)                                  # num_legislatura
    coligacao = models.ForeignKey(Coligacao, blank=True, null=True)               # cod_coligacao
    tipo_causa_fim_mandato = models.IntegerField(blank=True, null=True)           # tip_causa_fim_mandato
    data_fim_mandato = models.DateField(blank=True, null=True)                    # dat_fim_mandato
    numero_votos_recebidos = models.IntegerField(blank=True, null=True)           # num_votos_recebidos
    data_expedicao_diploma = models.DateField(blank=True, null=True)              # dat_expedicao_diploma
    txt_observacao = models.TextField(blank=True, null=True)                      # txt_observacao


class CargoMesa(models.Model):
    nome = models.CharField(max_length=50)  # des_cargo
    unico = models.BooleanField()           # ind_unico


class ComposicaoMesa(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)               # cod_parlamentar
    sessao_legislativa = models.ForeignKey(SessaoLegislativa)  # cod_sessao_leg
    cargo = models.ForeignKey(CargoMesa)                       # cod_cargo
