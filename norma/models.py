from django.db import models
from django.utils.translation import ugettext_lazy as _

from materia.models import MateriaLegislativa
from sapl.utils import make_choices


class AssuntoNorma(models.Model):
    assunto = models.CharField(max_length=50, verbose_name=_('Assunto'))
    descricao = models.CharField(
        max_length=250, blank=True, null=True, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Assunto de Norma')
        verbose_name_plural = _('Assuntos de Norma')

    def __str__(self):
        return self.assunto


class TipoNormaJuridica(models.Model):
    # TODO transform into Domain Model and use an FK for the field
    EQUIVALENTE_LEXML_CHOICES = ((name, name) for name in
                                 ('constituicao',
                                  'ementa.constitucional',
                                  'lei.complementar',
                                  'lei.delegada',
                                  'lei',
                                  'decreto.lei',
                                  'medida.provisoria',
                                  'decreto',
                                  'lei.organica',
                                  'emenda.lei.organica',
                                  'decreto.legislativo',
                                  'resolucao',
                                  'regimento.interno',
                                  ))
    equivalente_lexml = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Equivalente LexML'),
        choices=EQUIVALENTE_LEXML_CHOICES)
    sigla = models.CharField(max_length=3, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Norma Jurídica')
        verbose_name_plural = _('Tipos de Norma Jurídica')

    def __str__(self):
        return self.descricao


class NormaJuridica(models.Model):
    ESFERA_FEDERACAO_CHOICES, ESTADUAL, FEDERAL, MUNICIPAL = make_choices(
        'E', _('Estadual'),
        'F', _('Federal'),
        'M', _('Municipal'),
    )

    tipo = models.ForeignKey(TipoNormaJuridica, verbose_name=_('Tipo'))
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)
    numero = models.IntegerField(verbose_name=_('Número'))
    ano = models.SmallIntegerField(verbose_name=_('Ano'))
    esfera_federacao = models.CharField(
        max_length=1,
        verbose_name=_('Esfera Federação'),
        choices=ESFERA_FEDERACAO_CHOICES)
    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))
    data_publicacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Publicação'))
    veiculo_publicacao = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name=_('Veículo Publicação'))
    pagina_inicio_publicacao = models.IntegerField(
        blank=True, null=True, verbose_name=_('Pg. Início'))
    pagina_fim_publicacao = models.IntegerField(
        blank=True, null=True, verbose_name=_('Pg. Fim'))
    ementa = models.TextField(verbose_name=_('Ementa'))
    indexacao = models.TextField(
        blank=True, null=True, verbose_name=_('Indexação'))
    observacao = models.TextField(
        blank=True, null=True, verbose_name=_('Observação'))
    complemento = models.NullBooleanField(
        blank=True, verbose_name=_('Complementar ?'))
    # XXX was a CharField (attention on migrate)
    assunto = models.ForeignKey(AssuntoNorma)
    data_vigencia = models.DateField(blank=True, null=True)
    timestamp = models.DateTimeField()

    class Meta:
        verbose_name = _('Norma Jurídica')
        verbose_name_plural = _('Normas Jurídicas')

    def __str__(self):
        return _(u'%(tipo)s nº %(numero)s - %(materia)s - %(ano)s') % {
            'tipo': self.tipo,
            'numero': self.numero,
            'materia': self.materia,
            'ano': self.ano}


class LegislacaoCitada(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    norma = models.ForeignKey(NormaJuridica)
    disposicoes = models.CharField(
        max_length=15, blank=True, null=True, verbose_name=_('Disposição'))
    parte = models.CharField(
        max_length=8, blank=True, null=True, verbose_name=_('Parte'))
    livro = models.CharField(
        max_length=7, blank=True, null=True, verbose_name=_('Livro'))
    titulo = models.CharField(
        max_length=7, blank=True, null=True, verbose_name=_('Título'))
    capitulo = models.CharField(
        max_length=7, blank=True, null=True, verbose_name=_('Capítulo'))
    secao = models.CharField(
        max_length=7, blank=True, null=True, verbose_name=_('Seção'))
    subsecao = models.CharField(
        max_length=7, blank=True, null=True, verbose_name=_('Subseção'))
    artigo = models.CharField(
        max_length=4, blank=True, null=True, verbose_name=_('Artigo'))
    paragrafo = models.CharField(
        max_length=3, blank=True, null=True, verbose_name=_('Parágrafo'))
    inciso = models.CharField(
        max_length=10, blank=True, null=True, verbose_name=_('Inciso'))
    alinea = models.CharField(
        max_length=3, blank=True, null=True, verbose_name=_('Alínea'))
    item = models.CharField(
        max_length=3, blank=True, null=True, verbose_name=_('Item'))

    class Meta:
        verbose_name = _('Matéria Legislativa')
        verbose_name_plural = _('Matérias Legislativas')


class VinculoNormaJuridica(models.Model):
    TIPO_VINCULO_CHOICES = (
        ('A', 'Altera a norma'),
        ('R', 'Revoga a norma'),
        ('P', 'Revoga parcialmente a norma'),
        ('T', 'Revoga por consolidação a norma'),
        ('C', 'Norma correlata'),
        ('I', 'Suspende a execução da norma'),
        ('G', 'Regulamenta a norma'),
    )

    # TODO M2M ???
    norma_referente = models.ForeignKey(NormaJuridica, related_name='+')
    norma_referida = models.ForeignKey(NormaJuridica, related_name='+')
    tipo_vinculo = models.CharField(
        max_length=1, blank=True, null=True, choices=TIPO_VINCULO_CHOICES)

    class Meta:
        verbose_name = _('Vínculo entre Normas Jurídicas')
        verbose_name_plural = _('Vínculos entre Normas Jurídicas')

    def __str__(self):
        return _(u'Referente: %(referente)s \n'
                 'Referida: %(referida)s \nVínculo: %(vinculo)s') % {
            'referente': self.norma_referente,
            'referida': self.norma_referida,
            'vinculo': self.tipo_vinculo}
