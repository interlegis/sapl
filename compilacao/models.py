from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from norma.models import NormaJuridica
from sapl.utils import YES_NO_CHOICES


class TipoNota(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    modelo = models.TextField(
        blank=True, verbose_name=_('Modelo'))

    class Meta:
        verbose_name = _('Tipo de Nota')
        verbose_name_plural = _('Tipos de Nota')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


class TipoVide(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Tipo de Vide')
        verbose_name_plural = _('Tipos de Vide')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


class TipoDispositivo(models.Model):
    FNC1 = '1'
    FNCI = 'I'
    FNCi = 'i'
    FNCA = 'A'
    FNCa = 'a'
    FNC8 = '*'
    FNCN = 'N'
    FORMATO_NUMERACAO_CHOICES = (
        (FNC1, _('(1) Numérico')),
        (FNCI, _('(I) Romano Maiúsculo')),
        (FNCi, _('(i) Romano Minúsculo')),
        (FNCA, _('(A) Alfabético Maiúsculo')),
        (FNCa, _('(a) Alfabético Minúsculo')),
        (FNC8, _('Tópico - Sem contagem')),
        (FNCN, _('Sem renderização')),
    )

    nome = models.CharField(
        max_length=50, unique=True, verbose_name=_('Nome'))
    class_css = models.CharField(
        max_length=20,
        verbose_name=_('Classe CSS'))
    rotulo_prefixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Prefixo html do rótulo'))
    rotulo_prefixo_texto = models.CharField(
        blank=True,
        max_length=30,
        verbose_name=_('Prefixo de construção do rótulo'))
    rotulo_ordinal = models.IntegerField(
        verbose_name=_('Tipo de número do rótulo'))
    rotulo_separadores_variacao = models.CharField(
        blank=True,
        max_length=5,
        verbose_name=_('Separadores das Variações'))
    rotulo_sufixo_texto = models.CharField(
        blank=True,
        max_length=30,
        verbose_name=_('Sufixo de construção do rótulo'))
    rotulo_sufixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Sufixo html do rótulo'))
    texto_prefixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Prefixo html do texto'))
    texto_sufixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Sufixo html do texto'))
    nota_automatica_prefixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Prefixo html da nota automática'))
    nota_automatica_sufixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Sufixo html da nota automática'))
    contagem_continua = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Contagem contínua'))
    formato_variacao0 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Numeração'))
    formato_variacao1 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 1'))
    formato_variacao2 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 2'))
    formato_variacao3 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 3'))
    formato_variacao4 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 4'))
    formato_variacao5 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 5'))

    class Meta:
        verbose_name = _('Tipo de Dispositivo')
        verbose_name_plural = _('Tipos de Dispositivo')

    def __str__(self):
        return self.nome


class TipoPublicacao(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Tipo de Publicação')
        verbose_name_plural = _('Tipos de Publicação')

    def __str__(self):
        return self.sigla + ' - ' + self.nome


class VeiculoPublicacao(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=60, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Veículo de Publicação')
        verbose_name_plural = _('Veículos de Publicação')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


class Publicacao(models.Model):
    norma = models.ForeignKey(
        NormaJuridica, verbose_name=_('Norma Jurídica'))
    veiculo_publicacao = models.ForeignKey(
        VeiculoPublicacao, verbose_name=_('Veículo de Publicação'))
    tipo_publicacao = models.ForeignKey(
        TipoPublicacao, verbose_name=_('Tipo de Publicação'))
    publicacao = models.DateTimeField(verbose_name=_('Data de Publicação'))
    pagina_inicio = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Início'))
    pagina_fim = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Fim'))
    timestamp = models.DateTimeField()

    class Meta:
        verbose_name = _('Publicação')
        verbose_name_plural = _('Publicações')

    def __str__(self):
        return '%s: %s' % (self.veiculo_publicacao, self.publicacao)


class Dispositivo(models.Model):
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordem de Renderização'))
    ordem_bloco_atualizador = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordem de Renderização no Bloco Atualizador'))
    nivel = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Nível Estrutural'))

    dispositivo0 = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Número do Dispositivo'))
    dispositivo1 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Primeiro Nível de Variação'))
    dispositivo2 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Segundo Nível de Variação'))
    dispositivo3 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Terceiro Nível de Variação'))
    dispositivo4 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Quarto Nível de Variação'))
    dispositivo5 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Quinto Nível de Variação'))

    rotulo = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_('Rótulo'))
    texto = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Texto'))
    texto_atualizador = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Texto no Dispositivo Atualizador'))

    inicio_vigencia = models.DateField(
        verbose_name=_('Início de Vigência'))
    fim_vigencia = models.DateField(
        blank=True, null=True, verbose_name=_('Fim de Vigência'))

    inicio_eficacia = models.DateField(
        verbose_name=_('Início de Eficácia'))
    fim_eficacia = models.DateField(
        blank=True, null=True, verbose_name=_('Fim de Eficácia'))

    inconstitucionalidade = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Inconstitucionalidade'))
    # Relevant attribute only in altering norms
    visibilidade = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Visibilidade na Norma Publicada'))

    timestamp = models.DateTimeField()

    tipo_dispositivo = models.ForeignKey(
        TipoDispositivo,
        related_name='dispositivos_do_tipo_set',
        verbose_name=_('Tipo do Dispositivo'))

    publicacao = models.ForeignKey(
        Publicacao,
        blank=True, null=True, default=None, verbose_name=_('Publicação'))

    norma = models.ForeignKey(
        NormaJuridica,
        related_name='dispositivos_set',
        verbose_name=_('Norma Jurídica'))
    norma_publicada = models.ForeignKey(
        NormaJuridica,
        blank=True, null=True, default=None,
        related_name='dispositivos_alterados_pela_norma_set',
        verbose_name=_('Norma Jurídica Publicada'))

    dispositivo_subsequente = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='+',
        verbose_name=_('Dispositivo Subsequente'))
    dispositivo_substituido = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='+',
        verbose_name=_('Dispositivo Substituido'))
    dispositivo_pai = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivos_filhos_set',
        verbose_name=_('Dispositivo Pai'))
    dispositivo_vigencia = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='+',
        verbose_name=_('Dispositivo de Vigência'))
    dispositivo_atualizador = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivos_alterados_set',
        verbose_name=_('Dispositivo Atualizador'))

    class Meta:
        verbose_name = _('Dispositivo')
        verbose_name_plural = _('Dispositivos')
        ordering = ['norma', 'ordem']
        unique_together = (
            ('norma', 'ordem',),
            ('norma',
             'dispositivo0',
             'dispositivo1',
             'dispositivo2',
             'dispositivo3',
             'dispositivo4',
             'dispositivo5',
             'tipo_dispositivo',
             'dispositivo_pai',
             'publicacao',),
        )

    def __str__(self):
        return '%(rotulo)s - %(norma)s' % {
            'rotulo': (self.rotulo if self.rotulo else self.tipo_dispositivo),
            'norma': self.norma}


class Vide(models.Model):
    data_criacao = models.DateTimeField(verbose_name=_('Data de Criação'))
    texto = models.TextField(verbose_name=_('Texto do Vide'))

    tipo = models.ForeignKey(TipoVide, verbose_name=_('Tipo do Vide'))

    dispositivo_base = models.ForeignKey(
        Dispositivo,
        verbose_name=_('Dispositivo Base'),
        related_name='%(class)s_dispositivo_base')
    dispositivo_ref = models.ForeignKey(
        Dispositivo,
        related_name='%(class)s_dispositivo_ref',
        verbose_name=_('Dispositivo Referido'))

    class Meta:
        verbose_name = _('Vide')
        verbose_name_plural = _('Vides')

    def __str__(self):
        return _('Vide %s') % self.texto


class Nota(models.Model):
    NPRIV = 1
    NSTRL = 2
    NINST = 3
    NPUBL = 4
    PUBLICIDADE_CHOICES = (
        # Only the owner of the note has visibility.
        (NPRIV, _('Nota Privada')),
        # All of the same group have visibility.
        (NSTRL, _('Nota Setorial')),
        # All authenticated users have visibility.
        (NINST, _('Nota Institucional')),
        # All users have visibility.
        (NPUBL, _('Nota Pública')),
    )

    texto = models.TextField(verbose_name=_('Texto da Nota'))
    url_externa = models.CharField(
        max_length=1024,
        blank=True,
        verbose_name=_('Url externa'))

    data_criacao = models.DateTimeField(verbose_name=_('Data de Criação'))
    publicacao = models.DateTimeField(verbose_name=_('Data de Publicação'))
    efetifidade = models.DateTimeField(verbose_name=_('Data de Efeito'))

    tipo = models.ForeignKey(TipoNota, verbose_name=_('Tipo da Nota'))
    dispositivo = models.ForeignKey(
        Dispositivo,
        verbose_name=_('Dispositivo da Nota'))

    owner = models.ForeignKey(User, verbose_name=_('Dono da Nota'))
    publicidade = models.PositiveSmallIntegerField(
        choices=PUBLICIDADE_CHOICES,
        verbose_name=_('Nível de Publicidade'))

    class Meta:
        verbose_name = _('Nota')
        verbose_name_plural = _('Notas')

    def __str__(self):
        return '%s: %s' % (
            self.tipo,
            self.PUBLICIDADE_CHOICES[self.publicidade][1]
        )
