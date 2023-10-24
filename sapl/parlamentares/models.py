
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from image_cropping.fields import ImageCropField, ImageRatioField
from model_utils import Choices
from prompt_toolkit.key_binding.bindings.named_commands import self_insert

from sapl.base.models import Autor
from sapl.decorators import vigencia_atual
from sapl.utils import (LISTA_DE_UFS, YES_NO_CHOICES, SaplGenericRelation,
                        get_settings_auth_user_model,
                        intervalos_tem_intersecao,
                        restringe_tipos_de_arquivo_img, texto_upload_path)


class Legislatura(models.Model):
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    data_inicio = models.DateField(verbose_name=_('Data Início'))
    data_fim = models.DateField(verbose_name=_('Data Fim'))
    data_eleicao = models.DateField(verbose_name=_('Data Eleição'))

    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = _('Legislatura')
        verbose_name_plural = _('Legislaturas')
        ordering = ('-numero', '-data_inicio', '-data_fim')

    def atual(self):
        current_year = timezone.now().year
        if not self.data_fim:
            self.data_fim = timezone.now().date()
        return self.data_inicio.year <= current_year <= self.data_fim.year

    @vigencia_atual
    def __str__(self):
        if not self.data_fim:
            self.data_fim = timezone.now().date()
        return _('%(numero)sª (%(start)s - %(end)s)') % {
            'numero': self.numero,
            'start': self.data_inicio.year,
            'end': self.data_fim.year}


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

    @vigencia_atual
    def __str__(self):
        return _('%(numero)sº (%(inicio)s - %(fim)s)') % {
            'numero': self.numero,
            'inicio': self.data_inicio.year,
            'fim': self.data_fim.year}


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
        ordering = ('legislatura', 'nome')

    def __str__(self):
        return self.nome


def get_logo_media_path(instance, subpath, filename):
    return './sapl/partidos/%s/%s/%s' % (instance, subpath, filename)


def logo_upload_path(instance, filename):
    return get_logo_media_path(instance, 'logo', filename)


class Partido(models.Model):
    sigla = models.CharField(max_length=20, verbose_name=_('Sigla'))
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
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Partido')
        verbose_name_plural = _('Partidos')
        ordering = ['sigla', 'nome']

    def __str__(self):
        return _('%(sigla)s - %(nome)s') % {
            'sigla': self.sigla, 'nome': self.nome
        }


class ComposicaoColigacao(models.Model):
    # TODO M2M
    partido = models.ForeignKey(Partido,
                                on_delete=models.PROTECT,
                                verbose_name=_('Partidos da Coligação'))
    coligacao = models.ForeignKey(Coligacao, on_delete=models.PROTECT)

    class Meta:
        verbose_name = (_('Composição Coligação'))
        verbose_name_plural = (_('Composição Coligações'))
        ordering = ('partido',)

    def __str__(self):
        return _('%(partido)s - %(coligacao)s') % {
            'partido': self.partido, 'coligacao': self.coligacao
        }


class NivelInstrucao(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Nível de Instrução'))

    class Meta:
        ordering = ['descricao']
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
        ordering = ['descricao']

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
        max_length=20, blank=True, verbose_name=_('R.G.'))
    titulo_eleitor = models.CharField(
        max_length=25,
        blank=True,
        verbose_name=_('Título de Eleitor'))
    numero_gab_parlamentar = models.CharField(
        max_length=10, blank=True, verbose_name=_('Nº Gabinete'))
    telefone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefone'))
    telefone_celular = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefone Celular'))
    fax = models.CharField(
        max_length=50, blank=True, verbose_name=_('Fax'))
    endereco_residencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Endereço Residencial'))
    municipio_residencia = models.CharField(
        max_length=50, blank=True, verbose_name=_('Município'))
    uf_residencia = models.CharField(
        max_length=2, blank=True, choices=LISTA_DE_UFS, verbose_name=_('UF'))
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

    fotografia = ImageCropField(
        verbose_name=_('Fotografia'), upload_to=foto_upload_path,
        validators=[restringe_tipos_de_arquivo_img], null=True, blank=True)
    cropping = ImageRatioField(
        'fotografia', '128x128', verbose_name=_('Avatar'), size_warning=True,
        help_text=_('A configuração do Avatar '
                    'é possível após a atualização da fotografia.'))

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


class TipoDependente(models.Model):
    descricao = models.CharField(max_length=150, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Dependente')
        verbose_name_plural = _('Tipos de Dependente')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class Dependente(models.Model):
    FEMININO = 'F'
    MASCULINO = 'M'
    SEXO_CHOICE = ((FEMININO, _('Feminino')),
                   (MASCULINO, _('Masculino')))

    tipo = models.ForeignKey(TipoDependente, on_delete=models.PROTECT,
                             verbose_name=_('Tipo'))
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.CASCADE)
    nome = models.CharField(max_length=150, verbose_name=_('Nome'))
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
        ordering = ('parlamentar', 'nome')

    def __str__(self):
        return self.nome


class Filiacao(models.Model):
    data = models.DateField(verbose_name=_('Data Filiação'))
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.CASCADE)
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


class TipoAfastamento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    indicador = models.CharField(
        max_length=1, verbose_name=_('Indicador'), default='F',
        choices=[('A', _('Afastamento')),
                 ('F', _('Fim de Mandato')), ])
    dispositivo = models.CharField(
        max_length=50, blank=True, verbose_name=_('Dispositivo'))

    class Meta:
        verbose_name = _('Tipo de Afastamento')
        verbose_name_plural = _('Tipos de Afastamento')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class Mandato(models.Model):
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.CASCADE)
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
                                           blank=False,
                                           null=True)
    data_fim_mandato = models.DateField(verbose_name=_('Fim do Mandato'),
                                        blank=True,
                                        null=True)
    votos_recebidos = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Votos Recebidos (Mandato)'))
    data_expedicao_diploma = models.DateField(blank=True,
                                              null=True,
                                              verbose_name=_('Expedição do Diploma'))
    titular = models.BooleanField(
        db_index=True,
        default=True,
        choices=YES_NO_CHOICES,
        verbose_name=_('Parlamentar Titular'))

    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))

    class Meta:
        verbose_name = _('Mandato')
        verbose_name_plural = _('Mandatos')
        ordering = ('parlamentar', 'legislatura__numero')

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
                    f.data_desfiliacao or timezone.datetime.max.date())]


class CargoMesa(models.Model):
    # TODO M2M ????
    descricao = models.CharField(
        max_length=50, verbose_name=_('Cargo na Mesa'))
    unico = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Cargo Único'), default=True)
    id_ordenacao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Posição na Ordenação'),
    )

    class Meta:
        verbose_name = _('Cargo na Mesa')
        verbose_name_plural = _('Cargos na Mesa')
        ordering = ['id_ordenacao', 'unico', 'descricao']

    def __str__(self):
        return self.descricao


class MesaDiretora(models.Model):
    data_inicio = models.DateField(verbose_name=_('Data Início'), null=True)
    data_fim = models.DateField(verbose_name=_('Data Fim'), null=True)
    sessao_legislativa = models.ForeignKey(SessaoLegislativa,
                                           on_delete=models.PROTECT)
    descricao = models.TextField(verbose_name=_('Descrição'), blank=True)

    class Meta:
        verbose_name = _('Mesa Diretora')
        verbose_name_plural = _('Mesas Diretoras')
        ordering = ('-data_inicio', '-sessao_legislativa')

    def __str__(self):
        return _('Mesa da %(sessao)s sessao da %(legislatura)s Legislatura') % {
            'sessao': self.sessao_legislativa, 'legislatura': self.sessao_legislativa.legislatura
        }


class ComposicaoMesa(models.Model):
    # TODO M2M ???? Ternary?????
    parlamentar = models.ForeignKey(Parlamentar, on_delete=models.PROTECT)
    cargo = models.ForeignKey(CargoMesa, on_delete=models.PROTECT)
    mesa_diretora = models.ForeignKey(
        MesaDiretora, on_delete=models.PROTECT, null=True)

    class Meta:
        verbose_name = _('Ocupação de cargo na Mesa')
        verbose_name_plural = _('Ocupações de cargo na Mesa')
        ordering = ('cargo', 'parlamentar')

    def __str__(self):
        return _('%(parlamentar)s - %(cargo)s') % {
            'parlamentar': self.parlamentar, 'cargo': self.cargo
        }


class Frente(models.Model):
    '''
        * Uma frente agrupa vários parlamentares
        * Cada parlamentar pode fazer parte de uma ou mais frentes
        * Uma frente pode existir por mais de uma legislatura?
    '''
    nome = models.CharField(
        max_length=80,
        verbose_name=_('Nome da Frente'))
    descricao = models.TextField(blank=True, verbose_name=_('Descrição'))
    data_criacao = models.DateField(verbose_name=_('Data Criação'))
    data_extincao = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data Dissolução'))

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(
        Autor,
        related_query_name='frente_set',
        fields_search=(
            ('nome', '__icontains'),
            ('descricao', '__icontains'),
            ('frenteparlamentar__parlamentar__filiacao__partido__sigla', '__icontains'),
            ('frenteparlamentar__parlamentar__filiacao__partido__nome', '__icontains'),
        )
    )

    class Meta:
        verbose_name = _('Frente Parlamentar')
        verbose_name_plural = _('Frentes Parlamentares')
        ordering = ('nome', '-data_criacao')

    def get_parlamentares(self):
        return Parlamentar.objects.filter(ativo=True)

    def __str__(self):
        return self.nome


class FrenteCargo(models.Model):
    nome_cargo = models.CharField(
        max_length=80,
        verbose_name=_('Cargo de frente parlamentar'))
    cargo_unico = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Cargo único?'))

    class Meta:
        verbose_name = _('Cargo de Frente Parlamentar')
        verbose_name_plural = _('Cargos de Frente Parlamentar')
        ordering = ('cargo_unico', 'nome_cargo',)

    def __str__(self):
        return f"{self.nome_cargo}"


class FrenteParlamentar(models.Model):
    frente = models.ForeignKey(
        Frente,
        verbose_name=_('Frente parlamentar'),
        on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(
        Parlamentar,
        verbose_name=_('Parlamentar'),
        on_delete=models.CASCADE)
    cargo = models.ForeignKey(
        FrenteCargo,
        verbose_name=_('Cargo na frente parlamentar'),
        on_delete=models.PROTECT)
    data_entrada = models.DateField(verbose_name=_('Data Entrada'))
    data_saida = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data Saída'))

    class Meta:
        verbose_name = _('Parlamentar de frente parlamentar')
        verbose_name_plural = _('Parlamentares de frente parlamentar')
        ordering = ('frente', 'parlamentar', 'cargo')

    def __str__(self):
        return f"{self.parlamentar} - {self.cargo.nome_cargo} - {self.frente}"


class Votante(models.Model):
    parlamentar = models.ForeignKey(
        Parlamentar, verbose_name=_('Parlamentar'),
        on_delete=models.PROTECT, related_name='votante_set')
    user = models.ForeignKey(
        get_settings_auth_user_model(), on_delete=models.PROTECT,
        verbose_name=_('User'), related_name='votante_set')
    data = models.DateTimeField(
        verbose_name=_('Data'), auto_now_add=True,
        max_length=30, null=True, blank=True)

    class Meta:
        verbose_name = _('Usuário Votante')
        verbose_name_plural = _('Usuários Votantes')
        permissions = (
            ('can_vote', _('Can Vote')),
        )
        ordering = ('parlamentar', '-data')

    def __str__(self):
        return self.user.username


class Bloco(models.Model):
    '''
        * blocos podem existir por mais de uma legislatura
    '''
    nome = models.CharField(
        max_length=120,
        verbose_name=_('Nome do Bloco'))
    partidos = models.ManyToManyField(
        Partido,
        blank=True,
        verbose_name=_('Partidos'))
    data_criacao = models.DateField(
        blank=False, null=True,
        verbose_name=_('Data Criação'))
    data_extincao = models.DateField(
        blank=True, null=True,
        verbose_name=_('Data Dissolução'))
    descricao = models.TextField(
        blank=True,
        verbose_name=_('Descrição'))

    # campo conceitual de reversão genérica para o model Autor que dá a
    # o meio possível de localização de tipos de autores.
    autor = SaplGenericRelation(Autor,
                                related_query_name='bloco_set',
                                fields_search=(
                                    ('nome', '__icontains'),
                                    ('descricao', '__icontains'),
                                    ('partidos__sigla', '__icontains'),
                                    ('partidos__nome', '__icontains'),
                                ))

    class Meta:
        verbose_name = _('Bloco Parlamentar')
        verbose_name_plural = _('Blocos Parlamentares')
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class BlocoCargo(models.Model):
    nome_cargo = models.CharField(
        max_length=120,
        verbose_name=_('Cargo do bloco parlamentar'))
    cargo_unico = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Cargo único?'))

    class Meta:
        verbose_name = _('Cargo de Bloco Parlamentar')
        verbose_name_plural = _('Cargos de Bloco Parlamentar')
        ordering = ('cargo_unico', 'nome_cargo',)

    def __str__(self):
        return f"{self.nome_cargo}"


class BlocoMembro(models.Model):
    bloco = models.ForeignKey(
        Bloco,
        verbose_name=_('Bloco parlamentar'),
        on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(
        Parlamentar,
        verbose_name=_('Parlamentar'),
        on_delete=models.CASCADE)
    cargo = models.ForeignKey(
        BlocoCargo,
        verbose_name=_('Cargo na bloco parlamentar'),
        on_delete=models.PROTECT)
    data_entrada = models.DateField(verbose_name=_('Data Entrada'))
    data_saida = models.DateField(
        blank=True, null=True,
        verbose_name=_('Data Saída'))

    class Meta:
        verbose_name = _('Membro de bloco parlamentar')
        verbose_name_plural = _('Membros de bloco parlamentar')
        ordering = ('bloco', 'parlamentar', 'cargo')

    def __str__(self):
        return f"{self.parlamentar} - {self.cargo.nome_cargo} - {self.bloco}"
