# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _


class Legislatura(models.Model):
    data_inicio = models.DateField(verbose_name=_(u'Data Início'))
    data_fim = models.DateField(verbose_name=_(u'Data Fim'))
    data_eleicao = models.DateField(verbose_name=_(u'Data Eleição'))

    class Meta:
        verbose_name = _(u'Legislatura')
        verbose_name_plural = _(u'Legislaturas')


class SessaoLegislativa(models.Model):
    ORDINARIA = 'O'
    EXTRAORDINARIA = 'E'
    TIPO_SESSAO_CHOICES = ((ORDINARIA, _(u'Ordinária')),
                           (EXTRAORDINARIA, _(u'Extraordinária')))

    legislatura = models.ForeignKey(Legislatura)
    numero = models.IntegerField(verbose_name=_(u'Número'))
    tipo = models.CharField(max_length=1, verbose_name=_(u'Tipo'), choices=TIPO_SESSAO_CHOICES)
    data_inicio = models.DateField(verbose_name=_(u'Data Início'))
    data_fim = models.DateField(verbose_name=_(u'Data Fim'))
    data_inicio_intervalo = models.DateField(blank=True, null=True, verbose_name=_(u'Início Intervalo'))
    data_fim_intervalo = models.DateField(blank=True, null=True, verbose_name=_(u'Fim Intervalo'))

    class Meta:
        verbose_name = _(u'Sessão Legislativa')
        verbose_name_plural = _(u'Sessões Legislativas')


class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura, verbose_name=_(u'Legislatura'))
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))
    numero_votos = models.IntegerField(blank=True, null=True, verbose_name=_(u'Nº Votos Recebidos'))

    class Meta:
        verbose_name = _(u'Coligação')
        verbose_name_plural = _(u'Coligações')


class Partido(models.Model):
    sigla = models.CharField(max_length=9, verbose_name=_(u'Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))
    data_criacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Criação'))
    data_extincao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Extinção'))

    class Meta:
        verbose_name = _(u'Partido')
        verbose_name_plural = _(u'Partidos')


class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido)
    coligacao = models.ForeignKey(Coligacao)


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

    nome = models.CharField(max_length=50, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True, choices=UF_CHOICES)
    regiao = models.CharField(max_length=2, blank=True, null=True, choices=REGIAO_CHOICES)

    class Meta:
        verbose_name = _(u'Município')
        verbose_name_plural = _(u'Municípios')


class NivelInstrucao(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Nível de Instrução'))

    class Meta:
        verbose_name = _(u'Nível Instrução')
        verbose_name_plural = _(u'Níveis Instrução')

    def __unicode__(self):
        return self.nivel_instrucao


class SituacaoMilitar(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Situação Militar'))

    class Meta:
        verbose_name = _(u'Tipo Situação Militar')
        verbose_name_plural = _(u'Tipos Situações Militares')


class Parlamentar(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _(u'Feminino')),
                   (MASCULINO, _(u'Masculino')))

    nivel_instrucao = models.ForeignKey(NivelInstrucao, blank=True, null=True, verbose_name=_(u'Nível Instrução'))
    situacao_militar = models.ForeignKey(SituacaoMilitar, blank=True, null=True, verbose_name=_(u'Situação Militar'))
    nome_completo = models.CharField(max_length=50, verbose_name=_(u'Nome Completo'))
    nome_parlamentar = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Nome Parlamentar'))
    sexo = models.CharField(max_length=1, verbose_name=_(u'Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Nascimento'))
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_(u'C.P.F'))
    rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'R.G.'))
    titulo_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Título de Eleitor'))
    cod_casa = models.IntegerField()
    numero_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True, verbose_name=_(u'Nº Gabinete'))
    telefone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone'))
    fax = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Fax'))
    endereco_residencia = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Endereço Residencial'))
    municipio_residencia = models.ForeignKey(Municipio, blank=True, null=True, verbose_name=_(u'Município'))
    cep_residencia = models.CharField(max_length=9, blank=True, null=True, verbose_name=_(u'CEP'))
    telefone_residencia = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone Residencial'))
    fax_residencia = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Fax Residencial'))
    endereco_web = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'HomePage'))
    profissao = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Profissão'))
    email = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Correio Eletrônico'))
    locais_atuacao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Locais de Atuação'))
    ativo = models.BooleanField(verbose_name=_(u'Ativo na Casa?'))
    biografia = models.TextField(blank=True, null=True, verbose_name=_(u'Biografia'))
    unidade_deliberativa = models.BooleanField()

    class Meta:
        verbose_name = _(u'Parlamentar')
        verbose_name_plural = _(u'Parlamentares')

    def __unicode__(self):
        return self.nome_completo


class TipoDependente(models.Model):
    descricao = models.CharField(max_length=50)

    class Meta:
        verbose_name = _(u'Tipo de Dependente')
        verbose_name_plural = _(u'Tipos de Dependente')


class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _(u'Feminino')),
                  (MASCULINO, _(u'Masculino')))

    tipo = models.ForeignKey(TipoDependente, verbose_name=_(u'Tipo'))
    parlamentar = models.ForeignKey(Parlamentar)
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))
    sexo = models.CharField(max_length=1, verbose_name=_(u'Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Nascimento'))
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_(u'CPF'))
    rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'RG'))
    titulo_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_(u'Nº Título Eleitor'))

    class Meta:
        verbose_name = _(u'Dependente')
        verbose_name_plural = _(u'Dependentes')


class Filiacao(models.Model):
    data = models.DateField(verbose_name=_(u'Data Filiação'))
    parlamentar = models.ForeignKey(Parlamentar)
    partido = models.ForeignKey(Partido, verbose_name=_(u'Partido'))
    data_desfiliacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desfiliação'))

    class Meta:
        verbose_name = _(u'Filiação')
        verbose_name_plural = _(u'Filiações')


class TipoAfastamento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))
    afastamento = models.BooleanField(verbose_name=_(u'Indicador'))
    fim_mandato = models.BooleanField(verbose_name=_(u'Indicador'))
    dispositivo = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Dispositivo'))

    class Meta:
        verbose_name = _(u'Tipo de Afastamento')
        verbose_name_plural = _(u'Tipos de Afastamento')


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    tipo_afastamento = models.ForeignKey(TipoAfastamento, blank=True, null=True)
    legislatura = models.ForeignKey(Legislatura, verbose_name=_(u'Legislatura'))
    coligacao = models.ForeignKey(Coligacao, blank=True, null=True, verbose_name=_(u'Coligação'))
    # TODO what is this field??????
    tipo_causa_fim_mandato = models.IntegerField(blank=True, null=True)
    data_fim_mandato = models.DateField(blank=True, null=True, verbose_name=_(u'Fim do Mandato'))
    votos_recebidos = models.IntegerField(blank=True, null=True, verbose_name=_(u'Votos Recebidos'))
    data_expedicao_diploma = models.DateField(blank=True, null=True, verbose_name=_(u'Expedição do Diploma'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))

    class Meta:
        verbose_name = _(u'Mandato')
        verbose_name_plural = _(u'Mandatos')


class CargoMesa(models.Model):
    # TODO M2M ????
    descricao = models.CharField(max_length=50, verbose_name=_(u'Cargo na Mesa'))
    unico = models.BooleanField(verbose_name=_(u'Cargo Único'))

    class Meta:
        verbose_name = _(u'Cargo na Mesa')
        verbose_name_plural = _(u'Cargos na Mesa')


class ComposicaoMesa(models.Model):
    # TODO M2M ???? Ternary?????
    parlamentar = models.ForeignKey(Parlamentar)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa)
    cargo = models.ForeignKey(CargoMesa)

    class Meta:
        verbose_name = _(u'Ocupação de cargo na Mesa')
        verbose_name_plural = _(u'Ocupações de cargo na Mesa')
