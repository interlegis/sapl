from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
import reversion

from sapl.base.models import Autor
from sapl.utils import (INDICADOR_AFASTAMENTO, UF, YES_NO_CHOICES,
                        SaplGenericRelation, get_settings_auth_user_model,
                        intervalos_tem_intersecao,
                        restringe_tipos_de_arquivo_img, texto_upload_path)


@reversion.register()
class Legislatura(models.Model):
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_eleicao = models.DateField(verbose_name=_('Data Eleição'))

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = _('Legislatura')
        verbose_name_plural = _('Legislaturas')

    def atual(self):
        current_year = datetime.now().year
        return self.data_inicio.year <= current_year <= self.data_fim.year

    def __str__(self):
        current = ' (%s)' % _('Atual') if self.atual() else ''

        return _('%(numero)sª (%(start)s - %(end)s)%(current)s') % {
            'numero': self.numero,
            'start': self.data_inicio.year,
            'end': self.data_fim.year,
            'current': current}


@reversion.register()
class SessaoLegislativa(models.Model):
    TIPO_SESSAO_CHOICES = Choices(
        ('O', 'ordinaria', _('Ordinária')),
        ('E', 'extraordinaria', _('Extraordinária')),
    )

    legislatura = models.ForeignKey(
        Legislatura,
        on_delete=models.PROTECT,
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
        ordering = ['-data_inicio', '-data_fim']

    def __str__(self):
        return _('%(numero)sº (%(inicio)s - %(fim)s)') % {
            'numero': self.numero,
            'inicio': self.data_inicio.year,
            'fim': self.data_fim.year}


@reversion.register()
class Coligacao(models.Model):
    legislatura = models.ForeignKey(Legislatura,
                                    on_delete=models.PROTECT,
                                    verbose_name=_('Legislatura'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    numero_votos = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name=_('Nº Votos Recebidos (Coligação)'))

    class Meta:
        verbose_name = _('Coligação')
        verbose_name_plural = _('Coligações')

    def __str__(self):
        return self.nome


def get_logo_media_path(instance, subpath, filename):
    return './sapl/partidos/%s/%s/%s' % (instance, subpath, filename)


def logo_upload_path(instance, filename):
    return get_logo_media_path(instance, 'logo', filename)


@reversion.register()
class Partido(models.Model):
    sigla = models.CharField(max_length=9, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    data_criacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Criação'))
    data_extincao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Extinção'))
    logo_partido = models.ImageField(
        blank=True,
        null=True,
        upload_to=logo_upload_path,
        verbose_name=_('Logo Partido'),
        validators=[restringe_tipos_de_arquivo_img])

    class Meta:
        verbose_name = _('Partido')
        verbose_name_plural = _('Partidos')

    def __str__(self):
        return _('%(sigla)s - %(nome)s') % {
            'sigla': self.sigla, 'nome': self.nome
        }


@reversion.register()
class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido,
                                on_delete=models.PROTECT,
                                verbose_name=_('Partidos da Coligação'))
    coligacao = models.ForeignKey(Coligacao, on_delete=models.PROTECT)

    class Meta:
        verbose_name = (_('Composição Coligação'))
        verbose_name_plural = (_('Composição Coligações'))

    def __str__(self):
        return _('%(partido)s - %(coligacao)s') % {
            'partido': self.partido, 'coligacao': self.coligacao
        }


@reversion.register()
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


@reversion.register()
class NivelInstrucao(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Nível de Instrução'))

    class Meta:
        verbose_name = _('Nível Instrução')
        verbose_name_plural = _('Níveis Instrução')

    def __str__(self):
        return self.descricao


@reversion.register()
class SituacaoMilitar(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Situação Militar'))

    class Meta:
        verbose_name = _('Tipo Situação Militar')
        verbose_name_plural = _('Tipos Situações Militares')

    def __str__(self):
        return self.descricao


def foto_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath='')


def true_false_none(x):
    if x == 'True':
        return True
    elif x == 'False':
        return False
    else:
        return None


@reversion.register()
class Parlamentar(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    nivel_instrucao = models.ForeignKey(
        NivelInstrucao,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Nível Instrução'))
    situacao_militar = models.ForeignKey(
        SituacaoMilitar,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
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
        Municipio, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Município'))
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
    ativo = models.BooleanField(
        db_index=True,
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Ativo na Casa?'))
    biografia = models.TextField(
        blank=True, verbose_name=_('Biografia'))
    # XXX Esse atribuito foi colocado aqui para não atrapalhar a migração

    fotografia = models.ImageField(
        blank=True,
        null=True,
        upload_to=foto_upload_path,
        verbose_name=_('Fotografia'),
        validators=[restringe_tipos_de_arquivo_img])

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(
        Autor,
        related_query_name='parlamentar_set',
        fields_search=(
            # na primeira posição dever ser campo simples sem __
            ('nome_completo', '__icontains'),
            ('nome_parlamentar', '__icontains'),
            ('filiacao__partido__sigla', '__icontains'),
        ))

    class Meta:
        verbose_name = _('Parlamentar')
        verbose_name_plural = _('Parlamentares')
        ordering = ['nome_parlamentar']

    def __str__(self):
        return self.nome_parlamentar

    @property
    def filiacao_atual(self):
        ultima_filiacao = self.filiacao_set.order_by('-data').first()
        if ultima_filiacao and not ultima_filiacao.data_desfiliacao:
            return ultima_filiacao.partido.sigla
        else:
            return _('Sem Partido')

    @property
    def avatar_html(self):
        return '<img class="avatar-parlamentar" src='\
            + self.fotografia.url + '>'if self.fotografia else ''

    def delete(self, using=None, keep_parents=False):
        if self.fotografia:
            self.fotografia.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.fotografia:
            fotografia = self.fotografia
            self.fotografia = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.fotografia = fotografia

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


@reversion.register()
class TipoDependente(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Dependente')
        verbose_name_plural = _('Tipos de Dependente')

    def __str__(self):
        return self.descricao


@reversion.register()
class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    tipo = models.ForeignKey(TipoDependente, on_delete=models.PROTECT,
                             verbose_name=_('Tipo'))
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
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


@reversion.register()
class Filiacao(models.Model):
    data = models.DateField(verbose_name=_('Data Filiação'))
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
    partido = models.ForeignKey(Partido,
                                on_delete=models.PROTECT,
                                verbose_name=_('Partido'))
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


@reversion.register()
class TipoAfastamento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    indicador = models.CharField(
        max_length=1, verbose_name=_('Indicador'), default='F',
        choices=INDICADOR_AFASTAMENTO)
    dispositivo = models.CharField(
        max_length=50, blank=True, verbose_name=_('Dispositivo'))

    class Meta:
        verbose_name = _('Tipo de Afastamento')
        verbose_name_plural = _('Tipos de Afastamento')

    def __str__(self):
        return self.descricao


@reversion.register()
class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
    tipo_afastamento = models.ForeignKey(
        TipoAfastamento, blank=True, null=True, on_delete=models.PROTECT)
    legislatura = models.ForeignKey(Legislatura, on_delete=models.PROTECT,
                                    verbose_name=_('Legislatura'))
    coligacao = models.ForeignKey(
        Coligacao, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Coligação'))
    # TODO what is this field??????
    tipo_causa_fim_mandato = models.PositiveIntegerField(blank=True, null=True)
    data_inicio_mandato = models.DateField(verbose_name=_('Início do Mandato'),
                                           blank=True,
                                           null=True)
    data_fim_mandato = models.DateField(verbose_name=_('Fim do Mandato'),
                                        blank=True,
                                        null=True)
    votos_recebidos = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Votos Recebidos (Mandato)'))
    data_expedicao_diploma = models.DateField(
        verbose_name=_('Expedição do Diploma'))
    titular = models.BooleanField(
        db_index=True,
        default=True,
        choices=YES_NO_CHOICES,
        verbose_name=_('Vereador Titular'))

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


@reversion.register()
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


@reversion.register()
class ComposicaoMesa(models.Model):
    # TODO M2M ???? Ternary?????
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa,
                                           on_delete=models.PROTECT)
    cargo = models.ForeignKey(CargoMesa, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('Ocupação de cargo na Mesa')
        verbose_name_plural = _('Ocupações de cargo na Mesa')

    def __str__(self):
        return _('%(parlamentar)s - %(cargo)s') % {
            'parlamentar': self.parlamentar, 'cargo': self.cargo
        }


@reversion.register()
class Frente(models.Model):
    '''
        * Uma frente agrupa vários parlamentares
        * Cada parlamentar pode fazer parte de uma ou mais frentes
        * Uma frente pode existir por mais de uma legislatura?
    '''
    nome = models.CharField(
        max_length=80,
        verbose_name=_('Nome da Frente'))
    parlamentares = models.ManyToManyField(Parlamentar,
                                           blank=True,
                                           verbose_name=_('Parlamentares'))
    data_criacao = models.DateField(verbose_name=_('Data Criação'))
    data_extincao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Dissolução'))
    descricao = models.TextField(blank=True, verbose_name=_('Descrição'))

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(
        Autor,
        related_query_name='frente_set',
        fields_search=(
            ('nome', '__icontains'),
            ('descricao', '__icontains'),
            ('parlamentares__filiacao__partido__sigla', '__icontains'),
            ('parlamentares__filiacao__partido__nome', '__icontains'),
        ))

    class Meta:
        verbose_name = _('Frente')
        verbose_name_plural = _('Frentes')

    def get_parlamentares(self):
        return Parlamentar.objects.filter(ativo=True)

    def __str__(self):
        return self.nome


class Votante(models.Model):
    parlamentar = models.ForeignKey(
        Parlamentar, verbose_name=_('Parlamentar'),
        on_delete=models.PROTECT, related_name='parlamentar')
    user = models.ForeignKey(
        get_settings_auth_user_model(), on_delete=models.PROTECT,
        verbose_name=_('User'), related_name='user')
    data = models.DateTimeField(
        verbose_name=_('Data'), auto_now_add=True,
        max_length=30, null=True, blank=True)

    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        permissions = (
            ('can_vote', _('Can Vote')),
        )

    def __str__(self):
        return self.user.username
