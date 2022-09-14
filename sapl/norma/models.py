from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.template import defaultfilters
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from sapl.base.models import Autor
from sapl.compilacao.models import TextoArticulado
from sapl.materia.models import MateriaLegislativa, Orgao
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES,
                        restringe_tipos_de_arquivo_txt,
                        texto_upload_path,
                        get_settings_auth_user_model,
                        OverwriteStorage)


class AssuntoNorma(models.Model):
    assunto = models.CharField(max_length=50, verbose_name=_('Assunto'))
    descricao = models.CharField(
        max_length=250, blank=True, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Assunto de Norma Jurídica')
        verbose_name_plural = _('Assuntos de Normas Jurídicas')
        ordering = ['assunto']

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


class NormaJuridicaManager(models.Manager):

    use_for_related_fields = True

    def normas_sem_textos_articulados(self):
        qs = self.get_queryset()
        qs = qs.filter(texto_articulado__isnull=True)
        return qs

    def normas_com_textos_articulados_publicados(self):
        qs = self.get_queryset()
        qs = qs.filter(
            texto_articulado__editable_only_by_owners=False,
            texto_articulado__privacidade=0,
            texto_articulado__isnull=False
        )

        return qs

    def normas_com_textos_articulados_pendentes(self):
        qs = self.get_queryset()
        qs = qs.filter(
            texto_articulado__editable_only_by_owners=False)

        q = models.Q(
            texto_articulado__privacidade=0
        ) | models.Q(
            texto_articulado__isnull=True
        )
        qs = qs.exclude(q)

        for n in qs:
            ta = n.texto_articulado.first()
            count = ta.dispositivos_set.count()
            if count == 1:
                count = 0
            elif count == 2:
                d = ta.dispositivos_set.last()
                if d.auto_inserido or not d.texto or d.texto == n.ementa:
                    count = 0
            elif count == 3:
                ds = ta.dispositivos_set.all()
                if ds[1].auto_inserido and \
                        not d[2].dispositivo_pai and\
                        d[2].tipo_dispositivo.dispositivo_de_articulacao:
                    count = 0

            if not count:
                ta.dispositivos_set.filter(
                    dispositivo_pai__isnull=False).delete()
                ta.publicacao_set.all().delete()
                ta.delete()

        return qs


class NormaJuridica(models.Model):

    objects = NormaJuridicaManager()

    ESFERA_FEDERACAO_CHOICES = Choices(
        ('M', 'municipal', _('Municipal')),
        ('E', 'estadual', _('Estadual')),
        ('F', 'federal', _('Federal')),
    )

    texto_integral = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        upload_to=norma_upload_path,
        verbose_name=_('Texto Integral'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt])
    tipo = models.ForeignKey(
        TipoNormaJuridica,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo da Norma Jurídica'))
    materia = models.ForeignKey(
        MateriaLegislativa, blank=True, null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Matéria'),
        related_name='normajuridica_set')
    orgao = models.ForeignKey(
        Orgao, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Órgão'))
    numero = models.CharField(
        max_length=8,
        verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    esfera_federacao = models.CharField(
        max_length=1,
        verbose_name=_('Esfera Federação'),
        choices=ESFERA_FEDERACAO_CHOICES)
    data = models.DateField(blank=False, null=True, verbose_name=_('Data'))
    data_publicacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Publicação'))
    veiculo_publicacao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Veículo de Publicação'))
    pagina_inicio_publicacao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Início'))
    pagina_fim_publicacao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Fim'))
    ementa = models.TextField(verbose_name=_('Ementa'))
    indexacao = models.TextField(
        blank=True, verbose_name=_('Indexação'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    complemento = models.BooleanField(
        null=True,
        blank=True,
        default=False,
        verbose_name=_('Complementar ?'),
        choices=YES_NO_CHOICES
    )
    # XXX was a CharField (attention on migrate)
    assuntos = models.ManyToManyField(
        AssuntoNorma, blank=True,
        verbose_name=_('Assuntos'))
    data_vigencia = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Vigência'))
    timestamp = models.DateTimeField(null=True)

    texto_articulado = GenericRelation(
        TextoArticulado, related_query_name='texto_articulado')

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

    autores = models.ManyToManyField(
        Autor,
        through='AutoriaNorma',
        through_fields=('norma', 'autor'),
        symmetrical=False)

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Usuário'),
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    ip = models.CharField(
        verbose_name=_('IP'),
        max_length=60,
        blank=True,
        default=''
    )
    ultima_edicao = models.DateTimeField(
        verbose_name=_('Data e Hora da Edição'),
        blank=True, null=True
    )

    class Meta:
        verbose_name = _('Norma Jurídica')
        verbose_name_plural = _('Normas Jurídicas')
        ordering = ['-data', '-numero']

    def get_normas_relacionadas(self):
        principais = NormaRelacionada.objects.filter(
            norma_principal=self.id).order_by('norma_principal__data',
                                              'norma_relacionada__data')
        relacionadas = NormaRelacionada.objects.filter(
            norma_relacionada=self.id).order_by('norma_principal__data',
                                                'norma_relacionada__data')
        return (principais, relacionadas)

    def get_anexos_norma_juridica(self):
        anexos = AnexoNormaJuridica.objects.filter(
            norma=self.id)
        return anexos

    def __str__(self):
        numero_norma = self.numero
        if numero_norma.isnumeric():
            numero_norma = '{0:,}'.format(int(self.numero)).replace(',', '.')

        return _('%(tipo)s%(orgao_sigla)s nº %(numero)s, de %(data)s') % {
            'tipo': self.tipo,
            'orgao_sigla': f'-{self.orgao.sigla}' if self.orgao else '',
            'numero': numero_norma,
            'data': defaultfilters.date(self.data, "d \d\e F \d\e Y").lower()}

    @property
    def epigrafe(self):
        return self.__str__()

    def delete(self, using=None, keep_parents=False):
        texto_integral = self.texto_integral
        result = super().delete(using=using, keep_parents=keep_parents)

        if texto_integral:
            texto_integral.delete(save=False)

        return result

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


def get_ano_atual():
    return timezone.now().year


class NormaEstatisticas(models.Model):
    usuario = models.CharField(max_length=50)
    horario_acesso = models.DateTimeField(
        blank=True, null=True)
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS, default=get_ano_atual)
    norma = models.ForeignKey(NormaJuridica,
                              on_delete=models.CASCADE)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return _('Usuário: %(usuario)s, Norma: %(norma)s') % {
            'usuario': self.usuario, 'norma': self.norma}


class ViewNormasEstatisticas(models.Model):
    mais_acessadas = models.PositiveSmallIntegerField(
        verbose_name=_('Mais Acessadas'))
    ano_est = models.PositiveSmallIntegerField(
        verbose_name=_('Ano do Registro de Acesso'))
    mes_est = models.PositiveSmallIntegerField(
        verbose_name=_('Mês do Registro de Acesso'))

    norma_id = models.BigIntegerField(verbose_name=_('Id da Norma'))
    norma_count = models.PositiveSmallIntegerField(
        verbose_name=_('Mês do Registro de Acesso'))

    norma_numero = models.CharField(
        max_length=8, verbose_name=_('Número da Norma'))

    norma_ano = models.PositiveSmallIntegerField(
        verbose_name=_('Ano da Norma'))
    norma_ementa = models.TextField(verbose_name=_('Ementa'))
    norma_observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))

    norma_tipo_sigla = models.CharField(
        max_length=3,
        verbose_name=_('Sigla do Tipo da Norma'))

    norma_tipo_descricao = models.CharField(
        max_length=50, verbose_name=_('Descrição do Tipo da Norma'))

    norma_data = models.DateField(verbose_name=_('Data da Norma'))

    class Meta:
        managed = False
        db_table = "norma_viewnormasestatisticas"


class AutoriaNorma(models.Model):
    autor = models.ForeignKey(Autor,
                              verbose_name=_('Autor'),
                              on_delete=models.CASCADE)
    norma = models.ForeignKey(
        NormaJuridica, on_delete=models.CASCADE,
        verbose_name=_('Matéria Legislativa'))
    primeiro_autor = models.BooleanField(verbose_name=_('Primeiro Autor'),
                                         choices=YES_NO_CHOICES,
                                         default=False)

    class Meta:
        verbose_name = _('Autoria')
        verbose_name_plural = _('Autorias')
        unique_together = (('autor', 'norma'), )
        ordering = ('-primeiro_autor', 'autor__nome')

    def __str__(self):
        return _('Autoria: %(autor)s - %(norma)s') % {
            'autor': self.autor, 'norma': self.norma}


class LegislacaoCitada(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    norma = models.ForeignKey(NormaJuridica, on_delete=models.CASCADE)
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
        ordering = ('id',)

    def __str__(self):
        return str(self.norma)


class TipoVinculoNormaJuridica(models.Model):
    sigla = models.CharField(
        max_length=1, blank=True, verbose_name=_('Sigla'))
    descricao_ativa = models.CharField(
        max_length=50, blank=True, verbose_name=_('Descrição Ativa'))
    descricao_passiva = models.CharField(
        max_length=50, blank=True, verbose_name=_('Descrição Passiva'))
    revoga_integralmente = models.BooleanField(verbose_name=_('Revoga Integralmente?'),
                                               choices=YES_NO_CHOICES,
                                               default=False)

    class Meta:
        verbose_name = _('Tipo de Vínculo entre Normas Jurídicas')
        verbose_name_plural = _('Tipos de Vínculos entre Normas Jurídicas')
        ordering = ('id',)

    def __str__(self):
        return self.descricao_ativa


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
    resumo = models.TextField(
        blank=True,
        default="",
        verbose_name=_('Resumo'),
    )

    class Meta:
        verbose_name = _('Norma Relacionada')
        verbose_name_plural = _('Normas Relacionadas')
        ordering = ('norma_principal__data', 'norma_relacionada__data')

    def __str__(self):
        return _('Principal: %(norma_principal)s'
                 ' - Relacionada: %(norma_relacionada)s') % {
            'norma_principal': str(self.norma_principal),
            'norma_relacionada': str(self.norma_relacionada)}


class AnexoNormaJuridica(models.Model):
    norma = models.ForeignKey(
        NormaJuridica,
        related_name='norma',
        on_delete=models.PROTECT,
        verbose_name=_('Norma Juridica'))
    assunto_anexo = models.TextField(
        blank=True,
        default="",
        verbose_name=_('Assunto do Anexo'),
        max_length=250
    )
    anexo_arquivo = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        upload_to=norma_upload_path,
        verbose_name=_('Arquivo Anexo'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt])
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)

    class Meta:
        verbose_name = _('Anexo da Norma Juridica')
        verbose_name_plural = _('Anexos da Norma Juridica')
        ordering = ('id',)

    def __str__(self):
        return _('Anexo: %(anexo)s da norma %(norma)s') % {
            'anexo': self.anexo_arquivo, 'norma': self.norma}

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.anexo_arquivo:
            anexo_arquivo = self.anexo_arquivo
            self.anexo_arquivo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.anexo_arquivo = anexo_arquivo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)

    def delete(self, using=None, keep_parents=False):
        anexo_arquivo = self.anexo_arquivo
        result = super().delete(using=using, keep_parents=keep_parents)

        if anexo_arquivo:
            anexo_arquivo.delete(save=False)

        return result
