# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from sapl.utils import make_choices


class Legislatura(models.Model):
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_eleicao = models.DateField(verbose_name=_('Data Eleição'))

    class Meta:
        verbose_name = _('Legislatura')
        verbose_name_plural = _('Legislaturas')


class SessaoLegislativa(models.Model):
    TIPO_SESSAO_CHOICES, ORDINARIA, EXTRAORDINARIA = make_choices(
        'O', _('Ordinária'),
        'E', _('Extraordinária'),
    )

    legislatura = models.ForeignKey(Legislatura)
    numero = models.IntegerField(verbose_name=_('Número'))
    tipo = models.CharField(max_length=1, verbose_name=_('Tipo'), choices=TIPO_SESSAO_CHOICES)
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_inicio_intervalo = models.DateField(blank=True, null=True, verbose_name=_('Início Intervalo'))
    data_fim_intervalo = models.DateField(blank=True, null=True, verbose_name=_('Fim Intervalo'))

    class Meta:
        verbose_name = _('Sessão Legislativa')
        verbose_name_plural = _('Sessões Legislativas')


class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura, verbose_name=_('Legislatura'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    numero_votos = models.IntegerField(blank=True, null=True, verbose_name=_('Nº Votos Recebidos'))

    class Meta:
        verbose_name = _('Coligação')
        verbose_name_plural = _('Coligações')


class Partido(models.Model):
    sigla = models.CharField(max_length=9, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    data_criacao = models.DateField(blank=True, null=True, verbose_name=_('Data Criação'))
    data_extincao = models.DateField(blank=True, null=True, verbose_name=_('Data Extinção'))

    class Meta:
        verbose_name = _('Partido')
        verbose_name_plural = _('Partidos')


class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido)
    coligacao = models.ForeignKey(Coligacao)


class Municipio(models.Model):  # Localidade
    # TODO filter on migration leaving only cities

    REGIAO_CHOICES = (
        ('CO', 'Centro-Oeste'),
        ('NE', 'Nordeste'),
        ('NO', 'Norte'),
        ('SE', 'Sudeste'),  # TODO convert on migrate SD => SE
        ('SL', 'Sul'),
        ('EX', 'Exterior'),
    )

    UF_CHOICES = (
        ('AC', 'Acre'),
        ('AL', 'Alagoas'),
        ('AP', 'Amapá'),
        ('AM', 'Amazonas'),
        ('BA', 'Bahia'),
        ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'),
        ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'),
        ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'),
        ('PR', 'Paraná'),
        ('PB', 'Paraíba'),
        ('PA', 'Pará'),
        ('PE', 'Pernambuco'),
        ('PI', 'Piauí'),
        ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'),
        ('RO', 'Rondônia'),
        ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'),
        ('SE', 'Sergipe'),
        ('SP', 'São Paulo'),
        ('TO', 'Tocantins'),
        ('EX', 'Exterior'),
    )

    nome = models.CharField(max_length=50, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True, choices=UF_CHOICES)
    regiao = models.CharField(max_length=2, blank=True, null=True, choices=REGIAO_CHOICES)

    class Meta:
        verbose_name = _('Município')
        verbose_name_plural = _('Municípios')


class NivelInstrucao(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Nível de Instrução'))

    class Meta:
        verbose_name = _('Nível Instrução')
        verbose_name_plural = _('Níveis Instrução')

    def __str__(self):
        return self.nivel_instrucao


class SituacaoMilitar(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Situação Militar'))

    class Meta:
        verbose_name = _('Tipo Situação Militar')
        verbose_name_plural = _('Tipos Situações Militares')


class Parlamentar(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    nivel_instrucao = models.ForeignKey(NivelInstrucao, blank=True, null=True, verbose_name=_('Nível Instrução'))
    situacao_militar = models.ForeignKey(SituacaoMilitar, blank=True, null=True, verbose_name=_('Situação Militar'))
    nome_completo = models.CharField(max_length=50, verbose_name=_('Nome Completo'))
    nome_parlamentar = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Nome Parlamentar'))
    sexo = models.CharField(max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(blank=True, null=True, verbose_name=_('Data Nascimento'))
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_('C.P.F'))
    rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_('R.G.'))
    titulo_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_('Título de Eleitor'))
    cod_casa = models.IntegerField()
    numero_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True, verbose_name=_('Nº Gabinete'))
    telefone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Telefone'))
    fax = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Fax'))
    endereco_residencia = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Endereço Residencial'))
    municipio_residencia = models.ForeignKey(Municipio, blank=True, null=True, verbose_name=_('Município'))
    cep_residencia = models.CharField(max_length=9, blank=True, null=True, verbose_name=_('CEP'))
    telefone_residencia = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Telefone Residencial'))
    fax_residencia = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Fax Residencial'))
    endereco_web = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('HomePage'))
    profissao = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Profissão'))
    email = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Correio Eletrônico'))
    locais_atuacao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Locais de Atuação'))
    ativo = models.BooleanField(verbose_name=_('Ativo na Casa?'))
    biografia = models.TextField(blank=True, null=True, verbose_name=_('Biografia'))
    unidade_deliberativa = models.BooleanField()

    class Meta:
        verbose_name = _('Parlamentar')
        verbose_name_plural = _('Parlamentares')

    def __str__(self):
        return self.nome_completo


class TipoDependente(models.Model):
    descricao = models.CharField(max_length=50)

    class Meta:
        verbose_name = _('Tipo de Dependente')
        verbose_name_plural = _('Tipos de Dependente')


class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                  (MASCULINO, _('Masculino')))

    tipo = models.ForeignKey(TipoDependente, verbose_name=_('Tipo'))
    parlamentar = models.ForeignKey(Parlamentar)
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    sexo = models.CharField(max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(blank=True, null=True, verbose_name=_('Data Nascimento'))
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_('CPF'))
    rg = models.CharField(max_length=15, blank=True, null=True, verbose_name=_('RG'))
    titulo_eleitor = models.CharField(max_length=15, blank=True, null=True, verbose_name=_('Nº Título Eleitor'))

    class Meta:
        verbose_name = _('Dependente')
        verbose_name_plural = _('Dependentes')


class Filiacao(models.Model):
    data = models.DateField(verbose_name=_('Data Filiação'))
    parlamentar = models.ForeignKey(Parlamentar)
    partido = models.ForeignKey(Partido, verbose_name=_('Partido'))
    data_desfiliacao = models.DateField(blank=True, null=True, verbose_name=_('Data Desfiliação'))

    class Meta:
        verbose_name = _('Filiação')
        verbose_name_plural = _('Filiações')


class TipoAfastamento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    afastamento = models.BooleanField(verbose_name=_('Indicador'))
    fim_mandato = models.BooleanField(verbose_name=_('Indicador'))
    dispositivo = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Dispositivo'))

    class Meta:
        verbose_name = _('Tipo de Afastamento')
        verbose_name_plural = _('Tipos de Afastamento')


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    tipo_afastamento = models.ForeignKey(TipoAfastamento, blank=True, null=True)
    legislatura = models.ForeignKey(Legislatura, verbose_name=_('Legislatura'))
    coligacao = models.ForeignKey(Coligacao, blank=True, null=True, verbose_name=_('Coligação'))
    # TODO what is this field??????
    tipo_causa_fim_mandato = models.IntegerField(blank=True, null=True)
    data_fim_mandato = models.DateField(blank=True, null=True, verbose_name=_('Fim do Mandato'))
    votos_recebidos = models.IntegerField(blank=True, null=True, verbose_name=_('Votos Recebidos'))
    data_expedicao_diploma = models.DateField(blank=True, null=True, verbose_name=_('Expedição do Diploma'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Mandato')
        verbose_name_plural = _('Mandatos')


class CargoMesa(models.Model):
    # TODO M2M ????
    descricao = models.CharField(max_length=50, verbose_name=_('Cargo na Mesa'))
    unico = models.BooleanField(verbose_name=_('Cargo Único'))

    class Meta:
        verbose_name = _('Cargo na Mesa')
        verbose_name_plural = _('Cargos na Mesa')


class ComposicaoMesa(models.Model):
    # TODO M2M ???? Ternary?????
    parlamentar = models.ForeignKey(Parlamentar)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa)
    cargo = models.ForeignKey(CargoMesa)

    class Meta:
        verbose_name = _('Ocupação de cargo na Mesa')
        verbose_name_plural = _('Ocupações de cargo na Mesa')
