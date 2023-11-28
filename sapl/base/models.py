from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.signals import post_migrate
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _

from sapl.utils import (LISTA_DE_UFS, YES_NO_CHOICES,
                        get_settings_auth_user_model, models_with_gr_for_model)


DOC_ADM_OSTENSIVO = 'O'
DOC_ADM_RESTRITIVO = 'R'

TIPO_DOCUMENTO_ADMINISTRATIVO = ((DOC_ADM_OSTENSIVO, _('Ostensiva')),
                                 (DOC_ADM_RESTRITIVO, _('Restritiva')))

RELATORIO_ATOS_ACESSADOS = (('S', _('Sim')),
                            ('N', _('Não')))

SEQUENCIA_NUMERACAO_PROTOCOLO = (('A', _('Sequencial por ano')),
                                 ('L', _('Sequencial por legislatura')),
                                 ('U', _('Sequencial único')))

SEQUENCIA_NUMERACAO_PROPOSICAO = (('A', _('Sequencial por ano para cada autor')),
                                  ('B', _('Sequencial por ano indepententemente do autor')))

ESFERA_FEDERACAO_CHOICES = (('M', _('Municipal')),
                            ('E', _('Estadual')),
                            ('F', _('Federal')),
                            )

ASSINATURA_ATA_CHOICES = (
    ('M', _('Mesa Diretora da Sessão')),
    ('P', _('Apenas o Presidente da Sessão')),
    ('T', _('Todos os Parlamentares Presentes na Sessão')),
)

ORDENACAO_PESQUISA_MATERIA = (
    ('S', _('Alfabética por Sigla')),
    ('R', _('Sequência Regimental')),
)


class CasaLegislativa(models.Model):
    # TODO ajustar todos os max_length !!!!
    # cod_casa => id (pk)

    codigo = models.CharField(max_length=100,
                              blank=True,
                              verbose_name=_('Codigo'))
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=100, verbose_name=_('Sigla'))
    endereco = models.CharField(max_length=100, verbose_name=_('Endereço'))
    cep = models.CharField(max_length=100, verbose_name=_('CEP'))
    municipio = models.CharField(max_length=50, verbose_name=_('Município'))
    uf = models.CharField(max_length=2,
                          choices=LISTA_DE_UFS,
                          verbose_name=_('UF'))
    telefone = models.CharField(
        max_length=100, blank=True, verbose_name=_('Telefone'))
    fax = models.CharField(
        max_length=100, blank=True, verbose_name=_('Fax'))
    logotipo = models.ImageField(
        blank=True,
        upload_to='sapl/public/casa/logotipo/',
        verbose_name=_('Logotipo'))
    endereco_web = models.URLField(
        max_length=100, blank=True, verbose_name=_('HomePage'))
    email = models.EmailField(
        max_length=100, blank=True, verbose_name=_('E-mail'))
    informacao_geral = models.TextField(
        max_length=100,
        blank=True,
        verbose_name=_('Informação Geral'))

    class Meta:
        verbose_name = _('Casa Legislativa')
        verbose_name_plural = _('Casa Legislativa')
        ordering = ('id',)

    def __str__(self):
        return _('Casa Legislativa de %(municipio)s') % {
            'municipio': self.municipio}


class AppConfig(models.Model):

    POLITICA_PROTOCOLO_CHOICES = (
        ('O', _('Sempre Gerar Protocolo')),
        ('C', _('Perguntar se é pra gerar protocolo ao incorporar')),
        ('N', _('Nunca Protocolar ao incorporar uma proposição')),
    )

    # MANTENHA A SEQUÊNCIA EQUIVALENTE COM /sapl/templates/base/layout.yaml
    # AppConfig:

    # CONFIGURAÇÕES GERAIS
    # Linha 1 ------------
    esfera_federacao = models.CharField(
        max_length=1,
        blank=True,
        default="",
        verbose_name=_('Esfera Federação'),
        choices=ESFERA_FEDERACAO_CHOICES)

    # MÓDULO PARLAMENTARES

    # MÓDULO MESA DIRETORA

    # MÓDULO COMISSÕES

    # MÓDULO BANCADAS PARLAMENTARES

    # MÓDULO DOCUMENTOS ADMINISTRATIVOS
    # Linha 1 -------------------------
    documentos_administrativos = models.CharField(
        max_length=1,
        verbose_name=_('Visibilidade dos Documentos Administrativos'),
        choices=TIPO_DOCUMENTO_ADMINISTRATIVO, default='O')
    tramitacao_documento = models.BooleanField(
        verbose_name=_(
            'Tramitar documentos anexados junto com os documentos principais?'),
        choices=YES_NO_CHOICES, default=True)
    # Linha 2 -------------------------
    protocolo_manual = models.BooleanField(
        verbose_name=_('Permitir informe manual de data e hora de protocolo?'),
        choices=YES_NO_CHOICES, default=False)
    sequencia_numeracao_protocolo = models.CharField(
        max_length=1,
        verbose_name=_('Sequência de numeração de protocolos'),
        choices=SEQUENCIA_NUMERACAO_PROTOCOLO, default='A')
    inicio_numeracao_protocolo = models.PositiveIntegerField(
        verbose_name=_('Início da numeração de protocolo'),
        default=1
    )
    # Linha 3 -------------------------
    identificacao_de_documentos = models.CharField(
        max_length=254,
        verbose_name=_('Formato da identificação dos documentos'),
        default='{sigla} Nº {numero}/{ano}{-}{complemento} - {nome}',
        help_text="""
        Como mostrar a identificação dos documentos administrativos?
        Você pode usar um conjunto de combinações que pretender.
        Ao fazer sua edição, será mostrado logo abaixo o último documento cadastrado, como exemplo de resultado de sua edição.
        Em caso de erro, nenhum documento será mostrado e aparecerá apenas o formato padrão mínimo, que é este: "{sigla} Nº {numero}/{ano}{-}{complemento} - {nome}".
        Muito importante, use as chaves "{}", sem elas, você estará inserindo um texto qualquer e não o valor de um campo.
        Você pode combinar as seguintes campos: {sigla} {nome} {numero} {ano} {complemento} {assunto}
        Ainda pode ser usado {/}, {-}, {.} se você quiser que uma barra, traço, ou ponto
        seja adicionado apenas se o próximo campo que será usado tenha algum conteúdo
        (não use dois destes destes condicionais em sequência, somente o último será considerado).
        """
    )

    # MÓDULO PROPOSIÇÕES
    # Linha 1 ----------
    sequencia_numeracao_proposicao = models.CharField(
        max_length=1,
        verbose_name=_('Sequência de numeração de proposições'),
        choices=SEQUENCIA_NUMERACAO_PROPOSICAO, default='A')
    receber_recibo_proposicao = models.BooleanField(
        verbose_name=_('Protocolar proposição somente com recibo?'),
        choices=YES_NO_CHOICES, default=True)
    proposicao_incorporacao_obrigatoria = models.CharField(
        verbose_name=_('Regra de incorporação de proposições e protocolo'),
        max_length=1, choices=POLITICA_PROTOCOLO_CHOICES, default='O')
    escolher_numero_materia_proposicao = models.BooleanField(
        verbose_name=_(
            'Indicar número da matéria a ser gerada na proposição?'),
        choices=YES_NO_CHOICES, default=False)

    # MÓDULO MATÉRIA LEGISLATIVA
    # Linha 1 ------------------
    tramitacao_origem_fixa = models.BooleanField(
        verbose_name=_(
            'Fixar origem de novas tramitações como sendo a tramitação de destino da última tramitação?'),
        choices=YES_NO_CHOICES,
        default=True,
        help_text=_('Ao utilizar a opção NÂO, você compreende que os controles '
                    'de origem e destino das tramitações são anulados, '
                    'podendo seu operador registrar quaisquer origem e '
                    'destino para as tramitações. Se você colocar Não, '
                    'fizer tramitações aleatórias e voltar para SIM, '
                    'o destino da tramitação mais recente será utilizado '
                    'para a origem de uma nova inserção!'))
    tramitacao_materia = models.BooleanField(
        verbose_name=_(
            'Tramitar matérias anexadas junto com as matérias principais?'),
        choices=YES_NO_CHOICES, default=True)
    ordenacao_pesquisa_materia = models.CharField(
        max_length=1,
        verbose_name=_(
            'Ordenação de Pesquisa da Matéria?'),
        choices=ORDENACAO_PESQUISA_MATERIA, default='S')

    # MÓDULO NORMAS JURÍDICAS
    # MÓDULO TEXTOS ARTICULADOS
    # Linha 1 -----------------
    texto_articulado_proposicao = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Proposições'),
        choices=YES_NO_CHOICES, default=False)
    texto_articulado_materia = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Matérias'),
        choices=YES_NO_CHOICES, default=False)
    texto_articulado_norma = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Normas'),
        choices=YES_NO_CHOICES, default=True)

    # MÓDULO SESSÃO PLENÁRIA
    assinatura_ata = models.CharField(
        verbose_name=_('Quem deve assinar a ata'),
        max_length=1, choices=ASSINATURA_ATA_CHOICES, default='T')
    # MÓDULO PAINEL
    cronometro_discurso = models.DurationField(
        verbose_name=_('Cronômetro do Discurso'),
        blank=True,
        null=True)

    cronometro_aparte = models.DurationField(
        verbose_name=_('Cronômetro do Aparte'),
        blank=True,
        null=True)

    cronometro_ordem = models.DurationField(
        verbose_name=_('Cronômetro da Ordem'),
        blank=True,
        null=True)

    cronometro_consideracoes = models.DurationField(
        verbose_name=_('Cronômetro de Considerações Finais'),
        blank=True,
        null=True)

    mostrar_brasao_painel = models.BooleanField(
        default=False,
        verbose_name=_('Mostrar brasão da Casa no painel?'))

    mostrar_voto = models.BooleanField(
        verbose_name=_(
            'Exibir voto do Parlamentar antes de encerrar a votação?'),
        choices=YES_NO_CHOICES, default=False)

    # MÓDULO ESTATÍSTICAS DE ACESSO
    estatisticas_acesso_normas = models.CharField(
        max_length=1,
        verbose_name=_('Estatísticas de acesso a normas'),
        choices=RELATORIO_ATOS_ACESSADOS, default='N')

    # MÓDULO SEGURANÇA

    # MÓDULO LEXML

    # TODO: a ser implementado na versão 3.2
    # painel_aberto = models.BooleanField(
    #     verbose_name=_('Painel aberto para usuário anônimo'),
    #     choices=YES_NO_CHOICES, default=False)

    google_recaptcha_site_key = models.CharField(
        verbose_name=_('Chave pública gerada pelo Google Recaptcha'),
        max_length=256, default='')
    google_recaptcha_secret_key = models.CharField(
        verbose_name=_('Chave privada gerada pelo Google Recaptcha'),
        max_length=256, default='')

    google_analytics_id_metrica = models.CharField(
        verbose_name=_('ID da Métrica do Google Analytics'),
        max_length=256, default='')

    class Meta:
        verbose_name = _('Configurações da Aplicação')
        verbose_name_plural = _('Configurações da Aplicação')
        permissions = (
            ('menu_sistemas', _('Renderizar Menu Sistemas')),
            ('view_tabelas_auxiliares', _('Visualizar Tabelas Auxiliares')),
        )
        ordering = ('-id',)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        fields = self._meta.get_fields()
        for f in fields:
            if f.name != 'id' and not cache.get(f'sapl_{f.name}') is None:
                cache.set(f'sapl_{f.name}', getattr(self, f.name), 600)

        return models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    @classmethod
    def attr(cls, attr):
        value = cache.get(f'sapl_{attr}')
        if not value is None:
            return value

        config = AppConfig.objects.first()

        if not config:
            config = AppConfig()
            config.save()

        value = getattr(config, attr)
        cache.set(f'sapl_{attr}', value, 600)

        return value

    def __str__(self):
        return _('Configurações da Aplicação - %(id)s') % {
            'id': self.id}


class TipoAutor(models.Model):
    descricao = models.CharField(
        max_length=50,
        verbose_name=_('Descrição'),
        help_text=_(
            'Obs: Não crie tipos de autores semelhante aos tipos fixos. ')
    )

    content_type = models.OneToOneField(
        ContentType,
        null=True,
        default=None,
        verbose_name=_('Modelagem no SAPL'),
        on_delete=models.PROTECT)

    class Meta:
        ordering = ['descricao']
        verbose_name = _('Tipo de Autor')
        verbose_name_plural = _('Tipos de Autor')

    def __str__(self):
        return self.descricao


class Autor(models.Model):
    operadores = models.ManyToManyField(
        get_settings_auth_user_model(),
        through='OperadorAutor',
        through_fields=('autor', 'user'),
        symmetrical=False,
        related_name='autor_set',
        verbose_name='Operadores')

    tipo = models.ForeignKey(
        TipoAutor,
        verbose_name=_('Tipo do Autor'),
        on_delete=models.PROTECT)
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        default=None)
    autor_related = GenericForeignKey('content_type', 'object_id')
    nome = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('Nome do Autor'))
    cargo = models.CharField(
        max_length=50,
        blank=True)

    class Meta:
        verbose_name = _('Autor')
        verbose_name_plural = _('Autores')
        unique_together = (('content_type', 'object_id'), )
        ordering = ('nome',)

    def __str__(self):
        if self.autor_related:
            return str(self.autor_related)
        else:
            if self.nome:
                if self.cargo:
                    return '{} - {}'.format(self.nome, self.cargo)
                else:
                    return str(self.nome)

        return '?'


class OperadorAutor(models.Model):

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Operador do Autor'),
        related_name='operadorautor_set',
        on_delete=CASCADE)

    autor = models.ForeignKey(
        Autor,
        related_name='operadorautor_set',
        verbose_name=_('Autor'),
        on_delete=CASCADE)

    @property
    def user_name(self):
        return '%s - %s' % (
            self.autor,
            self.user)

    class Meta:
        verbose_name = _('Operador do Autor')
        verbose_name_plural = _('Operadores do Autor')
        unique_together = (
            ('user', 'autor', ),)

    def __str__(self):
        return self.user_name


class AuditLog(models.Model):

    operation = ('C', 'D', 'U')

    MAX_DATA_LENGTH = 4096  # 4KB de texto

    username = models.CharField(max_length=100,
                                verbose_name=_('username'),
                                blank=True,
                                db_index=True)
    operation = models.CharField(max_length=1,
                                 verbose_name=_('operation'),
                                 db_index=True)
    timestamp = models.DateTimeField(verbose_name=_('timestamp'),
                                     db_index=True)
    # DEPRECATED FIELD! TO BE REMOVED (EVENTUALLY)
    object = models.CharField(max_length=MAX_DATA_LENGTH,
                              blank=True,
                              verbose_name=_('object'))
    data = JSONField(null=True, verbose_name=_('data'))
    object_id = models.PositiveIntegerField(verbose_name=_('object_id'),
                                            db_index=True)
    model_name = models.CharField(max_length=100,
                                  verbose_name=_('model'),
                                  db_index=True)
    app_name = models.CharField(max_length=100,
                                verbose_name=_('app'),
                                db_index=True)

    class Meta:
        verbose_name = _('AuditLog')
        verbose_name_plural = _('AuditLogs')
        ordering = ('-id', '-timestamp')

    def __str__(self):
        return "[%s] %s %s.%s %s" % (self.timestamp,
                                     self.operation,
                                     self.app_name,
                                     self.model_name,
                                     self.username,
                                     )


class Metadata(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    class Meta:
        verbose_name = _('Metadado')
        verbose_name_plural = _('Metadados')
        unique_together = (('content_type', 'object_id'), )

    def __str__(self):
        return f'Metadata de {self.content_object}'
