
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import Concat
from django.template import defaultfilters
from django.utils import formats, timezone
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
import reversion

from sapl.base.models import SEQUENCIA_NUMERACAO_PROTOCOLO, Autor
from sapl.comissoes.models import Comissao, Reuniao
from sapl.compilacao.models import (PerfilEstruturalTextoArticulado,
                                    TextoArticulado)
from sapl.parlamentares.models import Parlamentar
#from sapl.protocoloadm.models import Protocolo
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES, SaplGenericForeignKey,
                        SaplGenericRelation, restringe_tipos_de_arquivo_txt,
                        texto_upload_path, get_settings_auth_user_model,
                        OverwriteStorage)


EM_TRAMITACAO = [(1, 'Sim'),
                 (0, 'Não')]


def grupo_autor():
    try:
        grupo = Group.objects.get(name='Autor')
    except Group.DoesNotExist:
        return None
    return grupo.id


@reversion.register()
class TipoProposicao(models.Model):
    descricao = models.CharField(
        max_length=50,
        verbose_name=_('Descrição'),
        unique=True,
        error_messages={
            'unique': _('Já existe um Tipo de Proposição com esta descrição.')
        })
    content_type = models.ForeignKey(
        ContentType, default=None,
        on_delete=models.PROTECT,
        verbose_name=_('Conversão de Meta-Tipos'),
        help_text=_("""
        Quando uma proposição é incorporada, ela é convertida de proposição
        para outro elemento dentro do Sapl. Existem alguns elementos que
        uma proposição pode se tornar. Defina este meta-tipo e em seguida
        escolha um Tipo Correspondente!
        """)
    )
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    tipo_conteudo_related = SaplGenericForeignKey(
        'content_type', 'object_id', verbose_name=_('Tipo Correspondente'))

    perfis = models.ManyToManyField(
        PerfilEstruturalTextoArticulado,
        blank=True, verbose_name=_('Perfis Estruturais de Textos Articulados'),
        help_text=_("""
                    Mesmo que em Configurações da Aplicação nas
                    Tabelas Auxiliares esteja definido que Proposições possam
                    utilizar Textos Articulados, ao gerar uma proposição,
                    a solução de Textos Articulados será disponibilizada se
                    o Tipo escolhido para a Proposição estiver associado a ao
                    menos um Perfil Estrutural de Texto Articulado.
                    """))

    class Meta:
        verbose_name = _('Tipo de Proposição')
        verbose_name_plural = _('Tipos de Proposições')

    def __str__(self):
        return self.descricao


class TipoMateriaManager(models.Manager):

    def reordene(self, exclude_pk=None):
        tipos = self.get_queryset()
        if exclude_pk:
            tipos = tipos.exclude(pk=exclude_pk)
        for sr, t in enumerate(tipos, 1):
            t.sequencia_regimental = sr
            t.save()

    def reposicione(self, pk, idx):
        tipos = self.reordene(exclude_pk=pk)

        self.get_queryset(
        ).filter(
            sequencia_regimental__gte=idx
        ).update(
            sequencia_regimental=models.F('sequencia_regimental') + 1
        )

        self.get_queryset(
        ).filter(
            pk=pk
        ).update(
            sequencia_regimental=idx
        )


@reversion.register()
class TipoMateriaLegislativa(models.Model):
    objects = TipoMateriaManager()
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição '))
    # XXX o que é isso ?
    num_automatica = models.BooleanField(default=False)
    # XXX o que é isso ?
    quorum_minimo_votacao = models.PositiveIntegerField(blank=True, null=True)

    tipo_proposicao = SaplGenericRelation(
        TipoProposicao,
        related_query_name='tipomaterialegislativa_set',
        fields_search=(
            ('descricao', '__icontains'),
            ('sigla', '__icontains')
        ))

    sequencia_numeracao = models.CharField(
        max_length=1,
        blank=True,
        verbose_name=_('Sequência de numeração'),
        choices=SEQUENCIA_NUMERACAO_PROTOCOLO)

    sequencia_regimental = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sequência Regimental'),
        help_text=_('A sequência regimental diz respeito ao que define '
                    'o regimento da Casa Legislativa sobre qual a ordem '
                    'de entrada das proposições nas Sessões Plenárias.'))

    class Meta:
        verbose_name = _('Tipo de Matéria Legislativa')
        verbose_name_plural = _('Tipos de Matérias Legislativas')
        ordering = ['sequencia_regimental', 'descricao']

    def __str__(self):
        return self.descricao


@reversion.register()
class RegimeTramitacao(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Regime de Tramitação')
        verbose_name_plural = _('Regimes de Tramitação')

    def __str__(self):
        return self.descricao


@reversion.register()
class Origem(models.Model):
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Origem')
        verbose_name_plural = _('Origens')

    def __str__(self):
        return self.nome


TIPO_APRESENTACAO_CHOICES = Choices(('O', 'oral', _('Oral')),
                                    ('E', 'escrita', _('Escrita')))


def materia_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.ano)


def anexo_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.materia.ano)


@reversion.register()
class MateriaLegislativa(models.Model):

    tipo = models.ForeignKey(
        TipoMateriaLegislativa,
        on_delete=models.PROTECT,
        verbose_name=TipoMateriaLegislativa._meta.verbose_name)
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)
    numero_protocolo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número do Protocolo'))
    data_apresentacao = models.DateField(
        verbose_name=_('Data de Apresentação'))
    tipo_apresentacao = models.CharField(
        max_length=1, blank=True,
        verbose_name=_('Tipo de Apresentação'),
        choices=TIPO_APRESENTACAO_CHOICES)
    regime_tramitacao = models.ForeignKey(
        RegimeTramitacao,
        on_delete=models.PROTECT,
        verbose_name=_('Regime Tramitação'))
    data_publicacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data de Publicação'))
    tipo_origem_externa = models.ForeignKey(
        TipoMateriaLegislativa,
        blank=True,
        null=True,
        related_name='tipo_origem_externa_set',
        on_delete=models.PROTECT,
        verbose_name=_('Tipo'))
    numero_origem_externa = models.CharField(
        max_length=10, blank=True, verbose_name=_('Número'))
    ano_origem_externa = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_('Ano'), choices=RANGE_ANOS)
    data_origem_externa = models.DateField(
        blank=True, null=True, verbose_name=_('Data'))
    local_origem_externa = models.ForeignKey(
        Origem, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Local de Origem'))
    apelido = models.CharField(
        max_length=50, blank=True, verbose_name=_('Apelido'))
    dias_prazo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Dias Prazo'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    em_tramitacao = models.BooleanField(
        verbose_name=_('Em Tramitação?'),
        default=False,
        choices=YES_NO_CHOICES)
    polemica = models.BooleanField(
        null=True,
        blank=True,
        default=False,
        verbose_name=_('Matéria Polêmica?')
    )
    objeto = models.CharField(
        max_length=150, blank=True, verbose_name=_('Objeto'))
    complementar = models.BooleanField(
        null=True,
        blank=True,
        default=False,
        verbose_name=_('É Complementar?')
    )
    ementa = models.TextField(verbose_name=_('Ementa'))
    indexacao = models.TextField(
        blank=True, verbose_name=_('Indexação'))
    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    resultado = models.TextField(blank=True)
    # XXX novo
    anexadas = models.ManyToManyField(
        'self',
        blank=True,
        through='Anexada',
        symmetrical=False,
        related_name='anexo_de',
        through_fields=(
            'materia_principal',
            'materia_anexada'))
    texto_original = models.FileField(
        max_length=300,
        blank=True,
        null=True,
        upload_to=materia_upload_path,
        verbose_name=_('Texto Original'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt])

    texto_articulado = GenericRelation(
        TextoArticulado, related_query_name='texto_articulado')

    proposicao = GenericRelation(
        'Proposicao', related_query_name='proposicao')

    autores = models.ManyToManyField(
        Autor,
        through='Autoria',
        through_fields=('materia', 'autor'),
        symmetrical=False,)

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

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
        verbose_name = _('Matéria Legislativa')
        verbose_name_plural = _('Matérias Legislativas')
        unique_together = (("tipo", "numero", "ano"),)
        ordering = ['-id']
        permissions = (("can_access_impressos", "Can access impressos"),)

    def __str__(self):
        return _('%(tipo)s nº %(numero)s de %(ano)s') % {
            'tipo': self.tipo, 'numero': self.numero, 'ano': self.ano}

    @property
    def epigrafe(self):
        return _('%(tipo)s nº %(numero)s de %(data)s') % {
            'tipo': self.tipo,
            'numero': self.numero,
            'data': defaultfilters.date(
                self.data_apresentacao,
                "d \d\e F \d\e Y"
            )}

    def data_entrada_protocolo(self):
        '''
           hack: recuperar a data de entrada do protocolo sem gerar
           dependência circular
        '''
        from sapl.protocoloadm.models import Protocolo
        if self.ano and self.numero_protocolo:
            protocolo = Protocolo.objects.filter(
                ano=self.ano,
                numero=self.numero_protocolo).first()
            if protocolo:
                if protocolo.timestamp:
                    return protocolo.timestamp.date()
                elif protocolo.timestamp_data_hora_manual:
                    return protocolo.timestamp_data_hora_manual.date()
                elif protocolo.data:
                    return protocolo.data

            return ''

    def delete(self, using=None, keep_parents=False):
        texto_original = self.texto_original
        result = super().delete(using=using, keep_parents=keep_parents)

        if texto_original:
            texto_original.delete(save=False)

        for p in self.proposicao.all():
            p.conteudo_gerado_related = None
            p.cancelado = True
            p.save()

        return result

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_original:
            texto_original = self.texto_original
            self.texto_original = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_original = texto_original

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


@reversion.register()
class Autoria(models.Model):
    autor = models.ForeignKey(Autor,
                              verbose_name=_('Autor'),
                              on_delete=models.PROTECT)
    materia = models.ForeignKey(
        MateriaLegislativa, on_delete=models.CASCADE,
        verbose_name=_('Matéria Legislativa'))
    primeiro_autor = models.BooleanField(verbose_name=_('Primeiro Autor'),
                                         choices=YES_NO_CHOICES,
                                         default=False)

    class Meta:
        verbose_name = _('Autoria')
        verbose_name_plural = _('Autorias')
        unique_together = (('autor', 'materia'), )
        ordering = ('-primeiro_autor', 'autor__nome')

    def __str__(self):
        return _('Autoria: %(autor)s - %(materia)s') % {
            'autor': self.autor, 'materia': self.materia}


@reversion.register()
class AcompanhamentoMateria(models.Model):
    usuario = models.CharField(max_length=50)
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    email = models.EmailField(
        max_length=100, verbose_name=_('E-mail'))
    data_cadastro = models.DateField(auto_now_add=True)
    hash = models.CharField(max_length=8)
    confirmado = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Acompanhamento de Matéria')
        verbose_name_plural = _('Acompanhamentos de Matéria')

    def __str__(self):
        if self.data_cadastro is None:
            return _('%(materia)s - %(email)s') % {
                'materia': self.materia,
                'email': self.email
            }
        else:
            return _('%(materia)s - %(email)s - Registrado em: %(data)s') % {
                'materia': self.materia,
                'email': self.email,
                'data': str(self.data_cadastro.strftime('%d/%m/%Y'))
            }


@reversion.register()
class PautaReuniao(models.Model):
    reuniao = models.ForeignKey(
        Reuniao, related_name='reuniao_set',
        on_delete=models.CASCADE,
        verbose_name=_('Reunião')
    )
    materia = models.ForeignKey(
        MateriaLegislativa, related_name='materia_set',
        on_delete=models.PROTECT,
        verbose_name=_('Matéria')
    )

    class Meta:
        verbose_name = _('Matéria da Pauta')
        verbose_name_plural = ('Matérias da Pauta')

    def __str__(self):
        return _('Reunião: %(reuniao)s'
                 ' - Matéria: %(materia)s') % {
                     'reuniao': self.reuniao,
                     'materia': self.materia
        }


@reversion.register()
class Anexada(models.Model):
    materia_principal = models.ForeignKey(
        MateriaLegislativa, related_name='materia_principal_set',
        on_delete=models.CASCADE,
        verbose_name=_('Matéria Principal'))
    materia_anexada = models.ForeignKey(
        MateriaLegislativa, related_name='materia_anexada_set',
        on_delete=models.CASCADE,
        verbose_name=_('Matéria Anexada'))
    data_anexacao = models.DateField(verbose_name=_('Data Anexação'))
    data_desanexacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desanexação'))

    class Meta:
        verbose_name = _('Anexada')
        verbose_name_plural = _('Anexadas')

    def __str__(self):
        return _('Principal: %(materia_principal)s'
                 ' - Anexada: %(materia_anexada)s') % {
            'materia_principal': self.materia_principal,
            'materia_anexada': self.materia_anexada}


@reversion.register()
class AssuntoMateria(models.Model):
    assunto = models.CharField(
        max_length=50,
        verbose_name=_('Assunto'))
    dispositivo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Descrição do Dispositivo Legal'))

    class Meta:
        verbose_name = _('Assunto de Matéria')
        verbose_name_plural = _('Assuntos de Matéria')
        ordering = ('assunto', 'dispositivo')

    def __str__(self):
        return self.assunto


@reversion.register()
class DespachoInicial(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    comissao = models.ForeignKey(
        Comissao, on_delete=models.CASCADE, verbose_name="Comissão")

    class Meta:
        verbose_name = _('Despacho Inicial')
        verbose_name_plural = _('Despachos Iniciais')

    def __str__(self):
        return _('%(materia)s - %(comissao)s') % {
            'materia': self.materia,
            'comissao': self.comissao}


@reversion.register()
class TipoDocumento(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Tipo Documento'))

    tipo_proposicao = SaplGenericRelation(
        TipoProposicao,
        related_query_name='tipodocumento_set',
        fields_search=(
            ('descricao', '__icontains'),
        ))

    class Meta:
        verbose_name = _('Tipo de Documento')
        verbose_name_plural = _('Tipos de Documento')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


@reversion.register()
class DocumentoAcessorio(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoDocumento,
                             on_delete=models.PROTECT,
                             verbose_name=_('Tipo'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    data = models.DateField(blank=True, null=True,
                            default=None, verbose_name=_('Data'))
    autor = models.CharField(
        max_length=200, blank=True, verbose_name=_('Autor'))
    ementa = models.TextField(blank=True, verbose_name=_('Ementa'))
    indexacao = models.TextField(blank=True)
    arquivo = models.FileField(
        blank=True,
        null=True,
        max_length=300,
        upload_to=anexo_upload_path,
        verbose_name=_('Texto Integral'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt])

    proposicao = GenericRelation(
        'Proposicao', related_query_name='proposicao')

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

    class Meta:
        verbose_name = _('Documento Acessório')
        verbose_name_plural = _('Documentos Acessórios')

    def __str__(self):
        return _('%(tipo)s - %(nome)s de %(data)s por %(autor)s') % {
            'tipo': self.tipo,
            'nome': self.nome,
            'data': formats.date_format(
                self.data, "SHORT_DATE_FORMAT") if self.data else '',
            'autor': self.autor}

    def delete(self, using=None, keep_parents=False):
        arquivo = self.arquivo
        result = super().delete(using=using, keep_parents=keep_parents)

        if arquivo:
            arquivo.delete(save=False)

        for p in self.proposicao.all():
            p.conteudo_gerado_related = None
            p.save()

        return result

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.arquivo = arquivo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


@reversion.register()
class MateriaAssunto(models.Model):
    # TODO M2M ??
    assunto = models.ForeignKey(
        AssuntoMateria,
        on_delete=models.CASCADE,
        verbose_name=_('Assunto'))
    materia = models.ForeignKey(
        MateriaLegislativa,
        on_delete=models.CASCADE,
        verbose_name=_('Matéria'))

    class Meta:
        verbose_name = _('Relação Matéria - Assunto')
        verbose_name_plural = _('Relações Matéria - Assunto')
        ordering = ('assunto__assunto', '-materia')

    def __str__(self):
        return _('%(materia)s - %(assunto)s') % {
            'materia': self.materia, 'assunto': self.assunto}


@reversion.register()
class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    tipo_materia = models.ForeignKey(
        TipoMateriaLegislativa,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Matéria'))
    numero_materia = models.CharField(max_length=5,
                                      verbose_name=_('Número'))
    ano_materia = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                                   choices=RANGE_ANOS)
    data_materia = models.DateField(verbose_name=_('Data'), null=True)

    class Meta:
        verbose_name = _('Numeração')
        verbose_name_plural = _('Numerações')
        ordering = ('materia',
                    'tipo_materia',
                    'numero_materia',
                    'ano_materia',
                    'data_materia',)

    def __str__(self):
        return _('%(numero)s/%(ano)s') % {
            'numero': self.numero_materia,
            'ano': self.ano_materia}


@reversion.register()
class Orgao(models.Model):
    nome = models.CharField(max_length=60, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    unidade_deliberativa = models.BooleanField(
        choices=YES_NO_CHOICES,
        verbose_name=(_('Unidade Deliberativa')),
        default=False)
    endereco = models.CharField(
        max_length=100, blank=True, verbose_name=_('Endereço'))
    telefone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefone'))

    autor = SaplGenericRelation(Autor,
                                related_query_name='orgao_set',
                                fields_search=(
                                    ('nome', '__icontains'),
                                    ('sigla', '__icontains')
                                ))

    class Meta:
        verbose_name = _('Órgão')
        verbose_name_plural = _('Órgãos')
        ordering = ['nome']

    def __str__(self):
        return _(
            '%(nome)s - %(sigla)s') % {'nome': self.nome, 'sigla': self.sigla}


@reversion.register()
class TipoFimRelatoria(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Tipo Fim Relatoria'))

    class Meta:
        verbose_name = _('Tipo Fim de Relatoria')
        verbose_name_plural = _('Tipos Fim de Relatoria')

    def __str__(self):
        return self.descricao


@reversion.register()
class Relatoria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    parlamentar = models.ForeignKey(Parlamentar,
                                    on_delete=models.CASCADE,
                                    verbose_name=_('Parlamentar'))
    tipo_fim_relatoria = models.ForeignKey(
        TipoFimRelatoria,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Motivo Fim Relatoria'))
    comissao = models.ForeignKey(
        Comissao, blank=True, null=True,
        on_delete=models.CASCADE, verbose_name=_('Comissão'))
    data_designacao_relator = models.DateField(
        verbose_name=_('Data Designação'))
    data_destituicao_relator = models.DateField(
        blank=True, null=True, verbose_name=_('Data Destituição'))

    class Meta:
        verbose_name = _('Relatoria')
        verbose_name_plural = _('Relatorias')

    def __str__(self):
        if self.tipo_fim_relatoria:
            return _('%(materia)s - %(tipo)s - %(data)s') % {
                'materia': self.materia,
                'tipo': self.tipo_fim_relatoria,
                'data': self.data_designacao_relator.strftime("%d/%m/%Y")}
        else:
            return _('%(materia)s - %(data)s') % {
                'materia': self.materia,
                'data': self.data_designacao_relator.strftime("%d/%m/%Y")}


@reversion.register()
class Parecer(models.Model):
    relatoria = models.ForeignKey(Relatoria, on_delete=models.CASCADE)
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    tipo_conclusao = models.CharField(max_length=3, blank=True)
    tipo_apresentacao = models.CharField(
        max_length=1, choices=TIPO_APRESENTACAO_CHOICES)
    parecer = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Parecer')
        verbose_name_plural = _('Pareceres')

    def __str__(self):
        return _('%(relatoria)s - %(tipo)s') % {
            'relatoria': self.relatoria, 'tipo': self.tipo_apresentacao
        }


@reversion.register()
class Proposicao(models.Model):
    autor = models.ForeignKey(
        Autor,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    tipo = models.ForeignKey(
        TipoProposicao,
        on_delete=models.PROTECT,
        blank=False,
        null=True,
        verbose_name=_('Tipo')
    )

    # XXX data_envio was not null, but actual data said otherwise!!!
    data_envio = models.DateTimeField(
        blank=False,
        null=True,
        verbose_name=_('Data de Envio')
    )

    data_recebimento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Data de Recebimento')
    )

    data_devolucao = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Data de Devolução')
    )

    descricao = models.TextField(verbose_name=_('Ementa'))

    justificativa_devolucao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Justificativa da Devolução')
    )

    ano = models.PositiveSmallIntegerField(
        verbose_name=_('Ano'),
        default=None,
        blank=True,
        null=True,
        choices=RANGE_ANOS
    )

    numero_proposicao = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Número')
    )

    numero_materia_futuro = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Número Matéria')
    )

    hash_code = models.CharField(
        verbose_name=_('Código do Documento'),
        max_length=200,
        blank=True
    )

    """
    FIXME Campo não é necessário na modelagem e implementação atual para o
    módulo de proposições.
    E - Enviada é tratado pela condição do campo data_envio - se None n enviado
        se possui uma data, enviada
    R - Recebida é uma condição do campo data_recebimento - se None não receb.
        se possui uma data, enviada, recebida e incorporada
    I - A incorporação é automática ao ser recebida

    e ainda possui a condição de Devolvida onde o campo data_devolucao é
    direfente de None, fornecedo a informação para o usuário da data que o
    responsável devolveu bem como a justificativa da devolução.
    Essa informação fica disponível para o Autor até que ele envie novamente
    sua proposição ou resolva excluir.
    """
    # ind_enviado and ind_devolvido collapsed as char field (status)
    status = models.CharField(
        blank=True,
        max_length=1,
        choices=(('E', 'Enviada'),
                 ('R', 'Recebida'),
                 ('I', 'Incorporada')),
        verbose_name=_('Status Proposição')
    )

    texto_original = models.FileField(
        max_length=300,
        upload_to=materia_upload_path,
        blank=True,
        null=True,
        verbose_name=_('Texto Original'),
        storage=OverwriteStorage(),
        validators=[restringe_tipos_de_arquivo_txt]
    )

    texto_articulado = GenericRelation(
        TextoArticulado,
        related_query_name='texto_articulado'
    )

    materia_de_vinculo = models.ForeignKey(
        MateriaLegislativa,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_('Matéria anexadora'),
        related_name=_('proposicao_set')
    )

    content_type = models.ForeignKey(
        ContentType,
        default=None,
        blank=True,
        null=True,
        verbose_name=_('Tipo de Material Gerado'),
        on_delete=models.PROTECT
    )

    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        default=None
    )

    conteudo_gerado_related = SaplGenericForeignKey(
        'content_type',
        'object_id',
        verbose_name=_('Conteúdo Gerado')
    )

    observacao = models.TextField(
        blank=True,
        verbose_name=_('Observação')
    )

    cancelado = models.BooleanField(
        verbose_name=_('Cancelada ?'),
        choices=YES_NO_CHOICES,
        default=False
    )

    """
    Ao ser recebida, irá gerar uma nova matéria ou um documento acessorio de uma já existente
    
    materia_gerada = models.ForeignKey(
        MateriaLegislativa,
        blank=True,
        null=True,
        related_name=_('materia_gerada')
    )
    documento_gerado = models.ForeignKey(
        DocumentoAcessorio,
        blank=True,
        null=True
    )
    """

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
        blank=True,
        null=True
    )

    @property
    def perfis(self):
        return self.tipo.perfis.all()

    @property
    def title_type(self):
        return '%s nº _____ %s' % (
            self.tipo, formats.date_format(
                self.data_envio if self.data_envio else timezone.now(),
                "\d\e d \d\e F \d\e Y"))

    class Meta:
        ordering = ['-data_recebimento']
        verbose_name = _('Proposição')
        verbose_name_plural = _('Proposições')
        unique_together = (('content_type', 'object_id'), )
        permissions = (
            ('detail_proposicao_enviada',
             _('Pode acessar detalhes de uma proposição enviada.')),
            ('detail_proposicao_devolvida',
             _('Pode acessar detalhes de uma proposição devolvida.')),
            ('detail_proposicao_incorporada',
             _('Pode acessar detalhes de uma proposição incorporada.')),
        )

    def __str__(self):
        if self.ano and self.numero_proposicao:
            return '%s %s/%s' % (Proposicao._meta.verbose_name,
                                 self.numero_proposicao,
                                 self.ano)
        else:
            if len(self.descricao) < 30:
                descricao = self.descricao[:28] + ' ...'
            else:
                descricao = self.descricao

            return '%s %s/%s' % (Proposicao._meta.verbose_name,
                                 self.id,
                                 descricao)

    @property
    def epigrafe(self):
        return _('%(tipo)s nº %(numero)s de %(data)s') % {
            'tipo': self.tipo,
            'numero': self.numero_proposicao,
            'data': defaultfilters.date(
                self.data_envio if self.data_envio else timezone.now(),
                "d \d\e F \d\e Y"
            )}

    def delete(self, using=None, keep_parents=False):
        texto_original = self.texto_original
        result = super().delete(using=using, keep_parents=keep_parents)

        if texto_original:
            texto_original.delete(save=False)

        return result

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_original:
            texto_original = self.texto_original
            self.texto_original = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_original = texto_original

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


@reversion.register()
class StatusTramitacao(models.Model):
    INDICADOR_CHOICES = Choices(('F', 'fim', _('Fim')),
                                ('R', 'retorno', _('Retorno')))

    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=60, verbose_name=_('Descrição'))
    indicador = models.CharField(
        blank=True,
        max_length=1, verbose_name=_('Indicador da Tramitação'),
        choices=INDICADOR_CHOICES)

    class Meta:
        verbose_name = _('Status de Tramitação')
        verbose_name_plural = _('Status de Tramitação')
        ordering = ['descricao']

    def __str__(self):
        return _('%(descricao)s') % {
            'descricao': self.descricao}


class UnidadeTramitacaoManager(models.Manager):
    """
        Esta classe permite ordenar alfabeticamente a unidade de tramitacao
        através da concatenação de 3 fields
    """

    def get_queryset(self):
        return super(UnidadeTramitacaoManager, self).get_queryset().annotate(
            nome_composto=Concat('orgao__nome',
                                 'comissao__sigla',
                                 'parlamentar__nome_parlamentar')
        ).order_by('nome_composto')


@reversion.register()
class UnidadeTramitacao(models.Model):
    comissao = models.ForeignKey(
        Comissao, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Comissão'))
    orgao = models.ForeignKey(
        Orgao, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Órgão'))
    parlamentar = models.ForeignKey(
        Parlamentar, blank=True, null=True,
        on_delete=models.PROTECT, verbose_name=_('Parlamentar'))

    objects = UnidadeTramitacaoManager()

    class Meta:
        verbose_name = _('Unidade de Tramitação')
        verbose_name_plural = _('Unidades de Tramitação')

    def __str__(self):
        if self.orgao and self.comissao and self.parlamentar:
            return _('%(comissao)s - %(orgao)s - %(parlamentar)s') % {
                'comissao': self.comissao, 'orgao': self.orgao,
                'parlamentar': self.parlamentar
            }
        elif self.orgao and self.comissao and not self.parlamentar:
            return _('%(comissao)s - %(orgao)s') % {
                'comissao': self.comissao, 'orgao': self.orgao
            }
        elif self.orgao and not self.comissao and self.parlamentar:
            return _('%(orgao)s - %(parlamentar)s') % {
                'orgao': self.orgao, 'parlamentar': self.parlamentar
            }
        elif not self.orgao and self.comissao and self.parlamentar:
            return _('%(comissao)s - %(parlamentar)s') % {
                'comissao': self.comissao, 'parlamentar': self.parlamentar
            }
        elif not self.orgao and self.comissao and not self.parlamentar:
            return _('%(comissao)s') % {'comissao': self.comissao}
        elif self.orgao and not self.comissao and not self.parlamentar:
            return _('%(orgao)s') % {'orgao': self.orgao}
        else:
            return _('%(parlamentar)s') % {'parlamentar': self.parlamentar}


@reversion.register()
class Tramitacao(models.Model):
    TURNO_CHOICES = Choices(
        ('P', 'primeiro', _('Primeiro')),
        ('S', 'segundo', _('Segundo')),
        ('U', 'unico', _('Único')),
        ('L', 'suplementar', _('Suplementar')),
        ('F', 'final', _('Final')),
        ('A', 'votacao_unica', _('Votação Única em Regime de Urgência')),
        ('B', 'primeira_votacao', _('1ª Votação')),
        ('C', 'segunda_terceira_votacao', _('2ª e 3ª Votações')),
        ('D', 'deliberacao', _('Deliberação')),
        ('G', 'primeria_segunda_votacoes', _('1ª e 2ª Votações')),
        ('E', 'primeira_segunda_votacao_urgencia', _(
            '1ª e 2ª Votações em Regime de Urgência')),

    )

    status = models.ForeignKey(StatusTramitacao, on_delete=models.PROTECT,
                               # TODO PÓS MIGRACAO INICIAL (vide #1381)
                               # não nulo quando todas as
                               # bases tiverem sido corrigidas
                               null=True,
                               verbose_name=_('Status'))
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.CASCADE)
    # TODO: Remover os campos de data
    # TODO: pois timestamp supre a necessidade
    timestamp = models.DateTimeField(default=timezone.now)
    data_tramitacao = models.DateField(verbose_name=_('Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(
        UnidadeTramitacao,
        related_name='tramitacoes_origem',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Local'))
    data_encaminhamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(
        UnidadeTramitacao,
        # TODO PÓS MIGRACAO INICIAL (vide #1381)
        # não nulo quando todas as
        # bases tiverem sido corrigidas
        null=True,
        related_name='tramitacoes_destino',
        on_delete=models.PROTECT,
        verbose_name=_('Unidade Destino'))
    urgente = models.BooleanField(verbose_name=_('Urgente ?'),
                                  choices=YES_NO_CHOICES,
                                  default=False)
    turno = models.CharField(
        max_length=1, blank=True, verbose_name=_('Turno'),
        choices=TURNO_CHOICES)
    texto = models.TextField(verbose_name=_('Texto da Ação'), blank=True)
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    user = models.ForeignKey(get_settings_auth_user_model(),
                             verbose_name=_('Usuário'),
                             on_delete=models.PROTECT,
                             null=True,
                             blank=True)
    ip = models.CharField(verbose_name=_('IP'),
                          max_length=60,
                          blank=True,
                          default='')
    ultima_edicao = models.DateTimeField(
        verbose_name=_('Data e Hora da Edição'),
        blank=True, null=True
    )

    class Meta:
        verbose_name = _('Tramitação')
        verbose_name_plural = _('Tramitações')

    def __str__(self):
        return _('%(materia)s | %(status)s | %(data)s') % {
            'materia': self.materia,
            'status': self.status,
            'data': self.data_tramitacao.strftime("%d/%m/%Y")}


class MateriaEmTramitacao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, on_delete=models.DO_NOTHING)
    tramitacao = models.ForeignKey(Tramitacao, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "materia_materiaemtramitacao"

    def __str__(self):
        return '{}/{}'.format(self.materia, self.tramitacao)

class ConfigEtiquetaMateriaLegislativa(models.Model):
    largura = models.FloatField(default=5)
    altura = models.FloatField(default=3)
        
    def save(self, *args, **kwargs):
        self.id = 1
        return super().save(*args, **kwargs)