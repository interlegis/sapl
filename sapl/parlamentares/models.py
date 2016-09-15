from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from sapl.utils import (UF, YES_NO_CHOICES, intervalos_tem_intersecao,
                        restringe_tipos_de_arquivo_img)


class Legislatura(models.Model):
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_eleicao = models.DateField(verbose_name=_('Data Eleição'))

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = _('Legislatura')
        verbose_name_plural = _('Legislaturas')

    def atual(self):
        current_year = datetime.now().year
        if(self.data_inicio.year <= current_year and
           self.data_fim.year >= current_year):
            return True
        else:
            return False

    def __str__(self):
        if self.atual():
            current = ' (%s)' % _('Atual')
        else:
            current = ''

        return _('%(id)sª (%(start)s - %(end)s)%(current)s') % {
            'id': self.id,
            'start': self.data_inicio.year,
            'end': self.data_fim.year,
            'current': current}


class SessaoLegislativa(models.Model):
    TIPO_SESSAO_CHOICES = Choices(
        ('O', 'ordinaria', _('Ordinária')),
        ('E', 'extraordinaria', _('Extraordinária')),
    )

    legislatura = models.ForeignKey(
        Legislatura,
        verbose_name=Legislatura._meta.verbose_name)
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    tipo = models.CharField(
        max_length=1, verbose_name=_('Tipo'), choices=TIPO_SESSAO_CHOICES)
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_inicio_intervalo = models.DateField(
        blank=True, null=True, verbose_name=_('Início Intervalo'))
    data_fim_intervalo = models.DateField(
        blank=True, null=True, verbose_name=_('Fim Intervalo'))

    class Meta:
        verbose_name = _('Sessão Legislativa')
        verbose_name_plural = _('Sessões Legislativas')

    def __str__(self):
        return _('%(id)sº (%(inicio)s - %(fim)s)') % {
            'id': self.id,
            'inicio': self.data_inicio.year,
            'fim': self.data_fim.year}


class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura, verbose_name=_('Legislatura'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    numero_votos = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Nº Votos Recebidos'))

    class Meta:
        verbose_name = _('Coligação')
        verbose_name_plural = _('Coligações')

    def __str__(self):
        return self.nome


class Partido(models.Model):
    sigla = models.CharField(max_length=9, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    data_criacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Criação'))
    data_extincao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Extinção'))

    class Meta:
        verbose_name = _('Partido')
        verbose_name_plural = _('Partidos')

    def __str__(self):
        return _('%(sigla)s - %(nome)s') % {
            'sigla': self.sigla, 'nome': self.nome
        }


class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido,
                                verbose_name=_('Partidos da Coligação'))
    coligacao = models.ForeignKey(Coligacao)

    class Meta:
        verbose_name = (_('Composição Coligação'))
        verbose_name_plural = (_('Composição Coligações'))

    def __str__(self):
        return _('%(partido)s - %(coligacao)s') % {
            'partido': self.partido, 'coligacao': self.coligacao
        }


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

    nome = models.CharField(max_length=50, blank=True)
    uf = models.CharField(
        max_length=2, blank=True, choices=UF)
    regiao = models.CharField(
        max_length=2, blank=True, choices=REGIAO_CHOICES)

    class Meta:
        verbose_name = _('Município')
        verbose_name_plural = _('Municípios')

    def __str__(self):
        return _('%(nome)s - %(uf)s (%(regiao)s)') % {
            'nome': self.nome, 'uf': self.uf, 'regiao': self.regiao
        }


class NivelInstrucao(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Nível de Instrução'))

    class Meta:
        verbose_name = _('Nível Instrução')
        verbose_name_plural = _('Níveis Instrução')

    def __str__(self):
        return self.descricao


class SituacaoMilitar(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Situação Militar'))

    class Meta:
        verbose_name = _('Tipo Situação Militar')
        verbose_name_plural = _('Tipos Situações Militares')

    def __str__(self):
        return self.descricao


def get_foto_media_path(instance, subpath, filename):
    return './sapl/parlamentar/%s/%s/%s' % (instance, subpath, filename)


def foto_upload_path(instance, filename):
    return get_foto_media_path(instance, 'foto', filename)


class Parlamentar(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        blank=True,
        null=True,
        verbose_name=_('Nível Instrução'))
    situacao_militar = models.ForeignKey(
        SituacaoMilitar,
        blank=True,
        null=True,
        verbose_name=_('Situação Militar'))
    nome_completo = models.CharField(
        max_length=50, verbose_name=_('Nome Completo'))
    nome_parlamentar = models.CharField(
        max_length=50,
        verbose_name=_('Nome Parlamentar'))
    sexo = models.CharField(
        max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Nascimento'))
    cpf = models.CharField(
        max_length=14, blank=True, verbose_name=_('C.P.F'))
    rg = models.CharField(
        max_length=15, blank=True, verbose_name=_('R.G.'))
    titulo_eleitor = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Título de Eleitor'))
    numero_gab_parlamentar = models.CharField(
        max_length=10, blank=True, verbose_name=_('Nº Gabinete'))
    telefone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefone'))
    fax = models.CharField(
        max_length=50, blank=True, verbose_name=_('Fax'))
    endereco_residencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Endereço Residencial'))
    municipio_residencia = models.ForeignKey(
        Municipio, blank=True, null=True, verbose_name=_('Município'))
    cep_residencia = models.CharField(
        max_length=9, blank=True, verbose_name=_('CEP'))
    telefone_residencia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Telefone Residencial'))
    fax_residencia = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Fax Residencial'))
    endereco_web = models.URLField(
        max_length=100, blank=True, verbose_name=_('HomePage'))
    profissao = models.CharField(
        max_length=50, blank=True, verbose_name=_('Profissão'))
    email = models.EmailField(
        max_length=100,
        blank=True,
        verbose_name=_('E-mail'))
    locais_atuacao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Locais de Atuação'))
    ativo = models.BooleanField(verbose_name=_('Ativo na Casa?'))
    biografia = models.TextField(
        blank=True, verbose_name=_('Biografia'))
    # XXX Esse atribuito foi colocado aqui para não atrapalhar a migração
    fotografia = models.ImageField(
        blank=True,
        null=True,
        upload_to=foto_upload_path,
        verbose_name=_('Fotografia'),
        validators=[restringe_tipos_de_arquivo_img])

    class Meta:
        verbose_name = _('Parlamentar')
        verbose_name_plural = _('Parlamentares')
        ordering = ['nome_parlamentar']

    def __str__(self):
        return self.nome_completo


class TipoDependente(models.Model):
    descricao = models.CharField(max_length=50)

    class Meta:
        verbose_name = _('Tipo de Dependente')
        verbose_name_plural = _('Tipos de Dependente')

    def __str__(self):
        return self.descricao


class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    tipo = models.ForeignKey(TipoDependente, verbose_name=_('Tipo'))
    parlamentar = models.ForeignKey(Parlamentar)
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    sexo = models.CharField(
        max_length=1, verbose_name=_('Sexo'), choices=SEXO_CHOICE)
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Nascimento'))
    cpf = models.CharField(
        max_length=14, blank=True, verbose_name=_('CPF'))
    rg = models.CharField(
        max_length=15, blank=True, verbose_name=_('RG'))
    titulo_eleitor = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('Nº Título Eleitor'))

    class Meta:
        verbose_name = _('Dependente')
        verbose_name_plural = _('Dependentes')

    def __str__(self):
        return self.nome


class Filiacao(models.Model):
    data = models.DateField(verbose_name=_('Data Filiação'))
    parlamentar = models.ForeignKey(Parlamentar)
    partido = models.ForeignKey(Partido, verbose_name=_('Partido'))
    data_desfiliacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desfiliação'))

    class Meta:
        verbose_name = _('Filiação')
        verbose_name_plural = _('Filiações')
        # A ordenação descrescente por data é importante para listagem de
        # parlamentares e tela de Filiações do Parlamentar
        ordering = ('parlamentar', '-data', '-data_desfiliacao')

    def __str__(self):
        return _('%(parlamentar)s - %(partido)s') % {
            'parlamentar': self.parlamentar, 'partido': self.partido
        }


class TipoAfastamento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    afastamento = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Indicador'))
    fim_mandato = models.BooleanField(verbose_name=_('Indicador'))
    dispositivo = models.CharField(
        max_length=50, blank=True, verbose_name=_('Dispositivo'))

    class Meta:
        verbose_name = _('Tipo de Afastamento')
        verbose_name_plural = _('Tipos de Afastamento')

    def __str__(self):
        return self.descricao


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar)
    tipo_afastamento = models.ForeignKey(
        TipoAfastamento, blank=True, null=True)
    legislatura = models.ForeignKey(Legislatura, verbose_name=_('Legislatura'))
    coligacao = models.ForeignKey(
        Coligacao, blank=True, null=True, verbose_name=_('Coligação'))
    # TODO what is this field??????
    tipo_causa_fim_mandato = models.PositiveIntegerField(blank=True, null=True)
    data_fim_mandato = models.DateField(verbose_name=_('Fim do Mandato'))
    votos_recebidos = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Votos Recebidos'))
    data_expedicao_diploma = models.DateField(
        verbose_name=_('Expedição do Diploma'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Mandato')
        verbose_name_plural = _('Mandatos')

    def __str__(self):
        return _('%(parlamentar)s %(legislatura)s') % {
            'parlamentar': self.parlamentar, 'legislatura': self.legislatura
        }

    def get_partidos(self):
        filicacoes = Filiacao.objects.filter(
            parlamentar=self.parlamentar).order_by('data')
        return [f.partido.sigla
                for f in filicacoes
                if intervalos_tem_intersecao(
                    self.legislatura.data_inicio,
                    self.legislatura.data_fim,
                    f.data,
                    f.data_desfiliacao or datetime.max.date())]


class CargoMesa(models.Model):
    # TODO M2M ????
    descricao = models.CharField(
        max_length=50, verbose_name=_('Cargo na Mesa'))
    unico = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Cargo Único'))

    class Meta:
        verbose_name = _('Cargo na Mesa')
        verbose_name_plural = _('Cargos na Mesa')

    def __str__(self):
        return self.descricao


class ComposicaoMesa(models.Model):
    # TODO M2M ???? Ternary?????
    parlamentar = models.ForeignKey(Parlamentar)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa)
    cargo = models.ForeignKey(CargoMesa)

    class Meta:
        verbose_name = _('Ocupação de cargo na Mesa')
        verbose_name_plural = _('Ocupações de cargo na Mesa')

    def __str__(self):
        return _('%(parlamentar)s - %(cargo)s') % {
            'parlamentar': self.parlamentar, 'cargo': self.cargo
        }
