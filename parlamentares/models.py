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
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))                                   # nom_coligacao
    numero_votos = models.IntegerField(blank=True, null=True, verbose_name=_(u'Nº Votos Recebidos'))  # num_votos_coligacao

    class Meta:
        verbose_name = _(u'Coligação')
        verbose_name_plural = _(u'Coligações')


class Partido(models.Model):
    sigla = models.CharField(max_length=9, verbose_name=_(u'Sigla'))                   # sgl_partido
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))                    # nom_partido
    data_criacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Criação'))    # dat_criacao
    data_extincao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Extinção'))  # dat_extincao

    class Meta:
        verbose_name = _(u'Partido')
        verbose_name_plural = _(u'Partidos')


class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido)      # cod_partido
    coligacao = models.ForeignKey(Coligacao)  # cod_coligacao


class Municipio(models.Model):  # Localidade
    # TODO filter on migration leaving only cities

    REGIAO_CHOICES = (
        ('CO', u'Centro-Oeste'),
        ('NE', u'Nordeste'),
        ('NO', u'Norte'),
        ('SE', u'Sudeste'),  # TODO convert on migrate SD => SE
        ('SL', u'Sul'),
        ('EX', u'Exterior'),
    )

    UF_CHOICES = (
        ('AC', u'Acre'),
        ('AL', u'Alagoas'),
        ('AP', u'Amapá'),
        ('AM', u'Amazonas'),
        ('BA', u'Bahia'),
        ('CE', u'Ceará'),
        ('DF', u'Distrito Federal'),
        ('ES', u'Espírito Santo'),
        ('GO', u'Goiás'),
        ('MA', u'Maranhão'),
        ('MT', u'Mato Grosso'),
        ('MS', u'Mato Grosso do Sul'),
        ('MG', u'Minas Gerais'),
        ('PR', u'Paraná'),
        ('PB', u'Paraíba'),
        ('PA', u'Pará'),
        ('PE', u'Pernambuco'),
        ('PI', u'Piauí'),
        ('RJ', u'Rio de Janeiro'),
        ('RN', u'Rio Grande do Norte'),
        ('RS', u'Rio Grande do Sul'),
        ('RO', u'Rondônia'),
        ('RR', u'Roraima'),
        ('SC', u'Santa Catarina'),
        ('SE', u'Sergipe'),
        ('SP', u'São Paulo'),
        ('TO', u'Tocantins'),
        ('EX', u'Exterior'),
    )

    nome = models.CharField(max_length=50, blank=True, null=True)       # nom_localidade
    uf = models.CharField(max_length=2, blank=True, null=True, choices=UF_CHOICES)               # sgl_uf
    regiao = models.CharField(max_length=2, blank=True, null=True, choices=REGIAO_CHOICES)           # sgl_regiao

    class Meta:
        verbose_name = _(u'Município')
        verbose_name_plural = _(u'Municípios')


class NivelInstrucao(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Nível de Instrução'))  # des_nivel_instrucao

    class Meta:
        verbose_name = _(u'Nível Instrução')
        verbose_name_plural = _(u'Níveis Instrução')

    def __unicode__(self):
        return self.nivel_instrucao


class SituacaoMilitar(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Situação Militar'))  # des_tipo_situacao

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
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_(u'C.P.F'))                            # num_cpf
    rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'R.G.'))                              # num_rg
    titulo_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Título de Eleitor'))        # num_tit_eleitor
    cod_casa = models.IntegerField()                                                                                         # cod_casa
    numero_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True, verbose_name=_(u'Nº Gabinete'))          # num_gab_parlamentar
    telefone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone'))             # num_tel_parlamentar
    fax = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Fax'))                  # num_fax_parlamentar
    endereco_residencia = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Endereço Residencial'))  # end_residencial
    municipio_residencia = models.ForeignKey(Municipio, blank=True, null=True, verbose_name=_(u'Município'))                    # cod_localidade_resid
    cep_residencia = models.CharField(max_length=9, blank=True, null=True, verbose_name=_(u'CEP'))                         # num_cep_resid
    telefone_residencia = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone Residencial'))       # num_tel_resid
    fax_residencia = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Fax Residencial'))            # num_fax_resid
    endereco_web = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'HomePage'))                      # end_web
    profissao = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Profissão'))                    # nom_profissao
    email = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Correio Eletrônico'))          # end_email
    locais_atuacao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Locais de Atuação'))  # des_local_atuacao
    ativo = models.BooleanField(verbose_name=_(u'Ativo na Casa?'))                                                           # ind_ativo
    biografia = models.TextField(blank=True, null=True, verbose_name=_(u'Biografia'))                                    # txt_biografia
    unidade_deliberativa = models.BooleanField()                                                                                # ind_unid_deliberativa

    class Meta:
        verbose_name = _(u'Parlamentar')
        verbose_name_plural = _(u'Parlamentares')

    def __unicode__(self):
        return self.nome_completo


class TipoDependente(models.Model):
    descricao = models.CharField(max_length=50)  # des_tipo_dependente

    class Meta:
        verbose_name = _(u'Tipo de Dependente')
        verbose_name_plural = _(u'Tipos de Dependente')


class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _(u'Feminino')),
                  (MASCULINO, _(u'Masculino')))

    tipo = models.ForeignKey(TipoDependente, verbose_name=_(u'Tipo'))                                       # tip_dependente
    parlamentar = models.ForeignKey(Parlamentar)                                                                       # cod_parlamentar
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))                                         # nom_dependente
    sexo = models.CharField(max_length=1, verbose_name=_(u'Sexo'), choices=SEXO_CHOICE)                                                     # sex_dependente
    data_nascimento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Nascimento'))                      # dat_nascimento
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_(u'CPF'))                        # num_cpf
    rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'RG'))                          # num_rg
    titulo_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Nº Título Eleitor'))  # num_tit_eleitor

    class Meta:
        verbose_name = _(u'Dependente')
        verbose_name_plural = _(u'Dependentes')


class Filiacao(models.Model):
    data = models.DateField(verbose_name=_(u'Data Filiação'))                               # dat_filiacao
    parlamentar = models.ForeignKey(Parlamentar)                                                     # cod_parlamentar
    partido = models.ForeignKey(Partido, verbose_name=_(u'Partido'))                                 # cod_partido
    data_desfiliacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desfiliação'))  # dat_desfiliacao

    class Meta:
        verbose_name = _(u'Filiação')
        verbose_name_plural = _(u'Filiações')


class TipoAfastamento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))                         # des_afastamento
    afastamento = models.BooleanField(verbose_name=_(u'Indicador'))                                             # ind_afastamento
    fim_mandato = models.BooleanField(verbose_name=_(u'Indicador'))                                             # ind_fim_mandato
    dispositivo = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Dispositivo'))  # des_dispositivo

    class Meta:
        verbose_name = _(u'Tipo de Afastamento')
        verbose_name_plural = _(u'Tipos de Afastamento')


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)                                                               # cod_parlamentar
    tipo_afastamento = models.ForeignKey(TipoAfastamento, blank=True, null=True)                               # tip_afastamento
    legislatura = models.ForeignKey(Legislatura, verbose_name=_(u'Legislatura'))                               # num_legislatura
    coligacao = models.ForeignKey(Coligacao, blank=True, null=True, verbose_name=_(u'Coligação'))              # cod_coligacao
    # TODO what is this field??????
    tipo_causa_fim_mandato = models.IntegerField(blank=True, null=True)                                        # tip_causa_fim_mandato
    data_fim_mandato = models.DateField(blank=True, null=True, verbose_name=_(u'Fim do Mandato'))              # dat_fim_mandato
    votos_recebidos = models.IntegerField(blank=True, null=True, verbose_name=_(u'Votos Recebidos'))    # num_votos_recebidos
    data_expedicao_diploma = models.DateField(blank=True, null=True, verbose_name=_(u'Expedição do Diploma'))  # dat_expedicao_diploma
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))                    # txt_observacao

    class Meta:
        verbose_name = _(u'Mandato')
        verbose_name_plural = _(u'Mandatos')


class CargoMesa(models.Model):
    # TODO M2M ????
    descricao = models.CharField(max_length=50, verbose_name=_(u'Cargo na Mesa'))          # des_cargo
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
