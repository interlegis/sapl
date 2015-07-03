# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _


class Legislatura(models.Model):
    data_inicio = models.DateField(verbose_name=_(u'Data Início'))    # dat_inicio
    data_fim = models.DateField(verbose_name=_(u'Data Fim'))          # dat_fim
    data_eleicao = models.DateField(verbose_name=_(u'Data Eleição'))  # dat_eleicao

    class Meta:
        verbose_name = _(u'Legislatura')
        verbose_name_plural = _(u'Legislaturas')


class SessaoLegislativa(models.Model):
    ORDINARIA = 'O'
    EXTRAORDINARIA = 'E'
    TIPO_SESSAO_CHOICES = ((ORDINARIA, _(u'Ordinária')),
                          (EXTRAORDINARIA, _(u'Extraordinária')))

    legislatura = models.ForeignKey(Legislatura)                                                          # num_legislatura
    numero = models.IntegerField(verbose_name=_(u'Número'))                                               # num_sessao_leg
    tipo = models.CharField(max_length=1, verbose_name=_(u'Tipo'), choices=TIPO_SESSAO_CHOICES)                                        # tip_sessao_leg
    data_inicio = models.DateField(verbose_name=_(u'Data Início'))                                        # dat_inicio
    data_fim = models.DateField(verbose_name=_(u'Data Fim'))                                              # dat_fim
    data_inicio_intervalo = models.DateField(blank=True, null=True, verbose_name=_(u'Início Intervalo'))  # dat_inicio_intervalo
    data_fim_intervalo = models.DateField(blank=True, null=True, verbose_name=_(u'Fim Intervalo'))        # dat_fim_intervalo

    class Meta:
        verbose_name = _(u'Sessão Legislativa')
        verbose_name_plural = _(u'Sessões Legislativas')


class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura, verbose_name=_(u'Legislatura'))                                # num_legislatura
    nome_coligacao = models.CharField(max_length=50, verbose_name=_(u'Nome'))                                   # nom_coligacao
    numero_votos_coligacao = models.IntegerField(blank=True, null=True, verbose_name=_(u'Nº Votos Recebidos'))  # num_votos_coligacao

    class Meta:
        verbose_name = _(u'Coligação')
        verbose_name_plural = _(u'Coligações')


class Partido(models.Model):
    sigla_partido = models.CharField(max_length=9, verbose_name=_(u'Sigla'))                   # sgl_partido
    nome_partido = models.CharField(max_length=50, verbose_name=_(u'Nome'))                    # nom_partido
    data_criacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Criação'))    # dat_criacao
    data_extincao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Extinção'))  # dat_extincao

    class Meta:
        verbose_name = _(u'Partido')
        verbose_name_plural = _(u'Partidos')


class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido)      # cod_partido
    coligacao = models.ForeignKey(Coligacao)  # cod_coligacao


class Localidade(models.Model):
    nome_localidade = models.CharField(max_length=50, blank=True, null=True)       # nom_localidade
    nome_localidade_pesq = models.CharField(max_length=50, blank=True, null=True)  # nom_localidade_pesq
    tipo_localidade = models.CharField(max_length=1, blank=True, null=True)        # tip_localidade
    sigla_uf = models.CharField(max_length=2, blank=True, null=True)               # sgl_uf
    sigla_regiao = models.CharField(max_length=2, blank=True, null=True)           # sgl_regiao

    class Meta:
        verbose_name = _(u'Município')
        verbose_name_plural = _(u'Municípios')


class NivelInstrucao(models.Model):
    nivel_instrucao = models.CharField(max_length=50, verbose_name=_(u'Nível de Instrução'))  # des_nivel_instrucao

    class Meta:
        verbose_name = _(u'Nível Instrução')
        verbose_name_plural = _(u'Níveis Instrução')

    def __unicode__(self):
        return self.nivel_instrucao


class SituacaoMilitar(models.Model):
    descricao_tipo_situacao = models.CharField(max_length=50, verbose_name=_(u'Situação Militar'))  # des_tipo_situacao

    class Meta:
        verbose_name = _(u'Tipo Situação Militar')
        verbose_name_plural = _(u'Tipos Situações Militares')


class Parlamentar(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _(u'Feminino')),
                   (MASCULINO, _(u'Masculino')))

    nivel_instrucao = models.ForeignKey(NivelInstrucao, blank=True, null=True, verbose_name=_(u'Nível Instrução'))           # cod_nivel_instrucao
    situacao_militar = models.ForeignKey(SituacaoMilitar, blank=True, null=True, verbose_name=_(u'Situação Militar'))        # tip_situacao_militar
    nome_completo = models.CharField(max_length=50, verbose_name=_(u'Nome Completo'))                                        # nom_completo
    nome_parlamentar = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Nome Parlamentar'))           # nom_parlamentar
    sexo = models.CharField(max_length=1, verbose_name=_(u'Sexo'), choices=SEXO_CHOICE)                                                           # sex_parlamentar
    data_nascimento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Nascimento'))                            # dat_nascimento
    numero_cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_(u'C.P.F'))                            # num_cpf
    numero_rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'R.G.'))                              # num_rg
    numero_tit_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Título de Eleitor'))        # num_tit_eleitor
    cod_casa = models.IntegerField()                                                                                         # cod_casa
    numero_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True, verbose_name=_(u'Nº Gabinete'))          # num_gab_parlamentar
    numero_tel_parlamentar = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone'))             # num_tel_parlamentar
    numero_fax_parlamentar = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Fax'))                  # num_fax_parlamentar
    endereco_residencial = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Endereço Residencial'))  # end_residencial
    localidade_resid = models.ForeignKey(Localidade, blank=True, null=True, verbose_name=_(u'Município'))                    # cod_localidade_resid
    numero_cep_resid = models.CharField(max_length=9, blank=True, null=True, verbose_name=_(u'CEP'))                         # num_cep_resid
    numero_tel_resid = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone Residencial'))       # num_tel_resid
    numero_fax_resid = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Fax Residencial'))            # num_fax_resid
    endereco_web = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'HomePage'))                      # end_web
    nome_profissao = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Profissão'))                    # nom_profissao
    endereco_email = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Correio Eletrônico'))          # end_email
    descricao_local_atuacao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Locais de Atuação'))  # des_local_atuacao
    ativo = models.BooleanField(verbose_name=_(u'Ativo na Casa?'))                                                           # ind_ativo
    biografia = models.TextField(blank=True, null=True, verbose_name=_(u'Biografia'))                                    # txt_biografia
    unid_deliberativa = models.BooleanField()                                                                                # ind_unid_deliberativa

    class Meta:
        verbose_name = _(u'Parlamentar')
        verbose_name_plural = _(u'Parlamentares')

    def __unicode__(self):
        return self.nome_completo


class TipoDependente(models.Model):
    descricao_tipo_dependente = models.CharField(max_length=50)  # des_tipo_dependente

    class Meta:
        verbose_name = _(u'Tipo de Dependente')
        verbose_name_plural = _(u'Tipos de Dependente')


class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _(u'Feminino')),
                  (MASCULINO, _(u'Masculino')))

    tipo_dependente = models.ForeignKey(TipoDependente, verbose_name=_(u'Tipo'))                                       # tip_dependente
    parlamentar = models.ForeignKey(Parlamentar)                                                                       # cod_parlamentar
    nome_dependente = models.CharField(max_length=50, verbose_name=_(u'Nome'))                                         # nom_dependente
    sexo = models.CharField(max_length=1, verbose_name=_(u'Sexo'), choices=SEXO_CHOICE)                                                     # sex_dependente
    data_nascimento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Nascimento'))                      # dat_nascimento
    numero_cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_(u'CPF'))                        # num_cpf
    numero_rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'RG'))                          # num_rg
    numero_tit_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Nº Título Eleitor'))  # num_tit_eleitor

    class Meta:
        verbose_name = _(u'Dependente')
        verbose_name_plural = _(u'Dependentes')


class Filiacao(models.Model):
    data_filiacao = models.DateField(verbose_name=_(u'Data Filiação'))                               # dat_filiacao
    parlamentar = models.ForeignKey(Parlamentar)                                                     # cod_parlamentar
    partido = models.ForeignKey(Partido, verbose_name=_(u'Partido'))                                 # cod_partido
    data_desfiliacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desfiliação'))  # dat_desfiliacao

    class Meta:
        verbose_name = _(u'Filiação')
        verbose_name_plural = _(u'Filiações')


class TipoAfastamento(models.Model):
    descricao_afastamento = models.CharField(max_length=50, verbose_name=_(u'Descrição'))                         # des_afastamento
    afastamento = models.BooleanField(verbose_name=_(u'Indicador'))                                             # ind_afastamento
    fim_mandato = models.BooleanField(verbose_name=_(u'Indicador'))                                             # ind_fim_mandato
    descricao_dispositivo = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Dispositivo'))  # des_dispositivo

    class Meta:
        verbose_name = _(u'Tipo de Afastamento')
        verbose_name_plural = _(u'Tipos de Afastamento')


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)                                                               # cod_parlamentar
    tipo_afastamento = models.ForeignKey(TipoAfastamento, blank=True, null=True)                               # tip_afastamento
    legislatura = models.ForeignKey(Legislatura, verbose_name=_(u'Legislatura'))                               # num_legislatura
    coligacao = models.ForeignKey(Coligacao, blank=True, null=True, verbose_name=_(u'Coligação'))              # cod_coligacao
    tipo_causa_fim_mandato = models.IntegerField(blank=True, null=True)                                        # tip_causa_fim_mandato
    data_fim_mandato = models.DateField(blank=True, null=True, verbose_name=_(u'Fim do Mandato'))              # dat_fim_mandato
    numero_votos_recebidos = models.IntegerField(blank=True, null=True, verbose_name=_(u'Votos Recebidos'))    # num_votos_recebidos
    data_expedicao_diploma = models.DateField(blank=True, null=True, verbose_name=_(u'Expedição do Diploma'))  # dat_expedicao_diploma
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))                    # txt_observacao

    class Meta:
        verbose_name = _(u'Mandato')
        verbose_name_plural = _(u'Mandatos')


class CargoMesa(models.Model):
    # TODO M2M ????
    nome = models.CharField(max_length=50, verbose_name=_(u'Cargo na Mesa'))          # des_cargo
    unico = models.BooleanField(verbose_name=_(u'Cargo Único'))                   # ind_unico

    class Meta:
        verbose_name = _(u'Cargo na Mesa')
        verbose_name_plural = _(u'Cargos na Mesa')


class ComposicaoMesa(models.Model):
    # TODO M2M ???? Ternary?????
    parlamentar = models.ForeignKey(Parlamentar)               # cod_parlamentar
    sessao_legislativa = models.ForeignKey(SessaoLegislativa)  # cod_sessao_leg
    cargo = models.ForeignKey(CargoMesa)                       # cod_cargo

    class Meta:
        verbose_name = _(u'Ocupação de cargo na Mesa')
        verbose_name_plural = _(u'Ocupações de cargo na Mesa')
