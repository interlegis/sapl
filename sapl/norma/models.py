import reversion
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from sapl.compilacao.models import TextoArticulado
from sapl.materia.models import MateriaLegislativa
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES,
                        restringe_tipos_de_arquivo_txt, texto_upload_path)


@reversion.register()
class AssuntoNorma(models.Model):
    assunto = models.CharField(max_length=50, verbose_name=_('Assunto'))
    descricao = models.CharField(
        max_length=250, blank=True, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Assunto de Norma Jurídica')
        verbose_name_plural = _('Assuntos de Normas Jurídicas')

    def __str__(self):
        return self.assunto


@reversion.register()
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
        verbose_name=_('Equivalente LexML'),
        choices=EQUIVALENTE_LEXML_CHOICES)
    sigla = models.CharField(max_length=3, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Norma Jurídica')
        verbose_name_plural = _('Tipos de Norma Jurídica')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao

def norma_upload_path(instance, filename):
        return texto_upload_path(instance, filename, subpath=instance.ano)

@reversion.register()
class NormaJuridica(models.Model):
    ESFERA_FEDERACAO_CHOICES = Choices(
        ('E', 'estadual', _('Estadual')),
        ('F', 'federal', _('Federal')),
        ('M', 'municipal', _('Municipal')),
    )
    
    texto_integral = models.FileField(
        blank=True,
        null=True,
        upload_to=norma_upload_path,
        verbose_name=_('Texto Integral'),
        validators=[restringe_tipos_de_arquivo_txt])
    tipo = models.ForeignKey(
        TipoNormaJuridica,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo da Norma Juridica'))
    materia = models.ForeignKey(
        MateriaLegislativa, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Matéria'))
    numero = models.CharField(
        max_length=8,
        verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    esfera_federacao = models.CharField(
        max_length=1,
        verbose_name=_('Esfera Federação'),
        choices=ESFERA_FEDERACAO_CHOICES)
    data = models.DateField(verbose_name=_('Data'))
    data_publicacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Publicação'))
    veiculo_publicacao = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_('Veículo Publicação'))
    pagina_inicio_publicacao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Início'))
    pagina_fim_publicacao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Fim'))
    ementa = models.TextField(verbose_name=_('Ementa'))
    indexacao = models.TextField(
        blank=True, verbose_name=_('Indexação'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    complemento = models.NullBooleanField(
        blank=True, verbose_name=_('Complementar ?'),
        choices=YES_NO_CHOICES)
    # XXX was a CharField (attention on migrate)
    assuntos = models.ManyToManyField(
        AssuntoNorma, blank=True,
        verbose_name=_('Assuntos'))
    data_vigencia = models.DateField(blank=True, null=True)
    timestamp = models.DateTimeField()

    texto_articulado = GenericRelation(
        TextoArticulado, related_query_name='texto_articulado')

    class Meta:
        verbose_name = _('Norma Jurídica')
        verbose_name_plural = _('Normas Jurídicas')
        ordering = ['-data', '-numero']

    def get_normas_relacionadas(self):
        principais = NormaRelacionada.objects.filter(
                norma_principal=self.id)
        relacionadas = NormaRelacionada.objects.filter(
                norma_relacionada=self.id)
        return (principais, relacionadas)

    def __str__(self):
        return _('%(tipo)s nº %(numero)s de %(data)s') % {
            'tipo': self.tipo,
            'numero': self.numero,
            'data': defaultfilters.date(self.data, "d \d\e F \d\e Y")}

    def delete(self, using=None, keep_parents=False):
        if self.texto_integral:
            self.texto_integral.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_integral:
            texto_integral = self.texto_integral
            self.texto_integral = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_integral = texto_integral

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


@reversion.register()
class LegislacaoCitada(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.PROTECT)
    norma = models.ForeignKey(NormaJuridica, on_delete=models.PROTECT)
    disposicoes = models.CharField(
        max_length=15, blank=True, verbose_name=_('Disposição'))
    parte = models.CharField(
        max_length=8, blank=True, verbose_name=_('Parte'))
    livro = models.CharField(
        max_length=7, blank=True, verbose_name=_('Livro'))
    titulo = models.CharField(
        max_length=7, blank=True, verbose_name=_('Título'))
    capitulo = models.CharField(
        max_length=7, blank=True, verbose_name=_('Capítulo'))
    secao = models.CharField(
        max_length=7, blank=True, verbose_name=_('Seção'))
    subsecao = models.CharField(
        max_length=7, blank=True, verbose_name=_('Subseção'))
    artigo = models.CharField(
        max_length=4, blank=True, verbose_name=_('Artigo'))
    paragrafo = models.CharField(
        max_length=3, blank=True, verbose_name=_('Parágrafo'))
    inciso = models.CharField(
        max_length=10, blank=True, verbose_name=_('Inciso'))
    alinea = models.CharField(
        max_length=3, blank=True, verbose_name=_('Alínea'))
    item = models.CharField(
        max_length=3, blank=True, verbose_name=_('Item'))

    class Meta:
        verbose_name = _('Legislação')
        verbose_name_plural = _('Legislações')

    def __str__(self):
        return str(self.norma)


@reversion.register()
class TipoVinculoNormaJuridica(models.Model):
    sigla = models.CharField(
        max_length=1, blank=True, verbose_name=_('Sigla'))
    descricao_ativa = models.CharField(
        max_length=50, blank=True, verbose_name=_('Descrição Ativa'))
    descricao_passiva = models.CharField(
        max_length=50, blank=True, verbose_name=_('Descrição Passiva'))

    class Meta:
        verbose_name = _('Tipo de Vínculo entre Normas Jurídicas')
        verbose_name_plural = _('Tipos de Vínculos entre Normas Jurídicas')

    def __str__(self):
        return self.descricao_ativa


@reversion.register()
class NormaRelacionada(models.Model):
    norma_principal = models.ForeignKey(
        NormaJuridica,
        related_name='norma_principal',
        on_delete=models.PROTECT,
        verbose_name=_('Norma Principal'))
    norma_relacionada = models.ForeignKey(
        NormaJuridica,
        related_name='norma_relacionada',
        on_delete=models.PROTECT,
        verbose_name=_('Norma Relacionada'))
    tipo_vinculo = models.ForeignKey(
        TipoVinculoNormaJuridica,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Vínculo'))

    class Meta:
        verbose_name = _('Norma Relacionada')
        verbose_name_plural = _('Normas Relacionadas')

    def __str__(self):
        return _('Principal: %(norma_principal)s'
                 ' - Relacionada: %(norma_relacionada)s') % {
            'norma_principal': self.norma_principal,
            'norma_relacionada': self.norma_relacionada}
