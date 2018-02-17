import reversion
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_migrate
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _

from sapl.utils import (LISTA_DE_UFS, YES_NO_CHOICES,
                        get_settings_auth_user_model, models_with_gr_for_model)

TIPO_DOCUMENTO_ADMINISTRATIVO = (('O', _('Ostensivo')),
                                 ('R', _('Restritivo')))

SEQUENCIA_NUMERACAO = (('A', _('Sequencial por ano')),
                       ('L', _('Sequencial por legislatura')),
                       ('U', _('Sequencial único')))


@reversion.register()
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

    def __str__(self):
        return _('Casa Legislativa de %(municipio)s') % {
            'municipio': self.municipio}


@reversion.register()
class ProblemaMigracao(models.Model):
    content_type = models.ForeignKey(ContentType,
                                     verbose_name=_('Tipo de Content'))
    object_id = models.PositiveIntegerField(verbose_name=_('ID do Objeto'))
    content_object = GenericForeignKey('content_type', 'object_id')
    nome_campo = models.CharField(max_length=100,
                                  blank=True,
                                  verbose_name=_('Nome do(s) Campo(s)'))
    problema = models.CharField(max_length=300, verbose_name=_('Problema'))
    descricao = models.CharField(max_length=300, verbose_name=_('Descrição'))
    eh_stub = models.BooleanField(verbose_name=_('É stub?'))
    critico = models.BooleanField(
        default=False, verbose_name=_('Crítico'))

    class Meta:
        verbose_name = _('Problema na Migração')
        verbose_name_plural = _('Problemas na Migração')


@reversion.register()
class Constraint(models.Model):
    nome_tabela = models.CharField(
        max_length=50, verbose_name=_('Nome da tabela'))
    nome_constraint = models.CharField(
        max_length=100, verbose_name=_('Nome da constraint'))
    nome_model = models.CharField(
        max_length=50, verbose_name=_('Nome da model'))
    tipo_constraint = models.CharField(
        max_length=50, verbose_name=_('Tipo da constraint'))

    class Meta:
        verbose_name = _('Constraint removida')
        verbose_name_plural = _('Constraints removidas')


@reversion.register()
class Argumento(models.Model):
    constraint = models.ForeignKey(Constraint)
    argumento = models.CharField(
        max_length=50, verbose_name=_('Argumento'))

    class Meta:
        verbose_name = _('Argumento da constraint')
        verbose_name_plural = _('Argumentos da constraint')


@reversion.register()
class AppConfig(models.Model):

    POLITICA_PROTOCOLO_CHOICES = (
        ('O', _('Sempre Gerar Protocolo')),
        ('C', _('Perguntar se é pra gerar protocolo ao incorporar')),
        ('N', _('Nunca Protocolar ao incorporar uma proposição')),
    )

    documentos_administrativos = models.CharField(
        max_length=1,
        verbose_name=_('Ostensivo/Restritivo'),
        choices=TIPO_DOCUMENTO_ADMINISTRATIVO, default='O')

    sequencia_numeracao = models.CharField(
        max_length=1,
        verbose_name=_('Sequência de numeração'),
        choices=SEQUENCIA_NUMERACAO, default='A')

    # TODO: a ser implementado na versão 3.2
    # painel_aberto = models.BooleanField(
    #     verbose_name=_('Painel aberto para usuário anônimo'),
    #     choices=YES_NO_CHOICES, default=False)

    texto_articulado_proposicao = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Proposições'),
        choices=YES_NO_CHOICES, default=False)

    texto_articulado_materia = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Matérias'),
        choices=YES_NO_CHOICES, default=False)

    texto_articulado_norma = models.BooleanField(
        verbose_name=_('Usar Textos Articulados para Normas'),
        choices=YES_NO_CHOICES, default=True)

    proposicao_incorporacao_obrigatoria = models.CharField(
        verbose_name=_('Regra de incorporação de proposições e protocolo'),
        max_length=1, choices=POLITICA_PROTOCOLO_CHOICES, default='O')

    cronometro_discurso = models.TimeField(
        verbose_name=_('Cronômetro do Discurso'),
        blank=True,
        null=True)

    cronometro_aparte = models.TimeField(
        verbose_name=_('Cronômetro do Aparte'),
        blank=True,
        null=True)

    cronometro_ordem = models.TimeField(
        verbose_name=_('Cronômetro da Ordem'),
        blank=True,
        null=True)

    mostrar_brasao_painel = models.BooleanField(
        default=False,
        verbose_name=_('Mostrar brasão da Casa no painel?'))

    class Meta:
        verbose_name = _('Configurações da Aplicação')
        verbose_name_plural = _('Configurações da Aplicação')
        permissions = (
            ('menu_sistemas', _('Renderizar Menu Sistemas')),
            ('view_tabelas_auxiliares', _('Visualizar Tabelas Auxiliares')),
        )
        ordering = ('-id',)

    @classmethod
    def attr(cls, attr):
        config = AppConfig.objects.first()

        if not config:
            config = AppConfig()
            config.save()

        return getattr(config, attr)

    def __str__(self):
        return _('Configurações da Aplicação - %(id)s') % {
            'id': self.id}


@reversion.register()
class TipoAutor(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Descrição'),
        help_text=_('Obs: Não crie tipos de autores '
                    'semelhante aos tipos fixos. '))

    content_type = models.OneToOneField(
        ContentType,
        null=True, default=None,
        verbose_name=_('Modelagem no SAPL'))

    class Meta:
        ordering = ['descricao']
        verbose_name = _('Tipo de Autor')
        verbose_name_plural = _('Tipos de Autor')

    def __str__(self):
        return self.descricao


@reversion.register()
class Autor(models.Model):

    user = models.OneToOneField(get_settings_auth_user_model(),
                                on_delete=models.SET_NULL,
                                null=True)

    tipo = models.ForeignKey(TipoAutor, verbose_name=_('Tipo do Autor'))

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    autor_related = GenericForeignKey('content_type', 'object_id')

    nome = models.CharField(
        max_length=60, blank=True, verbose_name=_('Nome do Autor'))

    cargo = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = _('Autor')
        verbose_name_plural = _('Autores')
        unique_together = (('content_type', 'object_id'), )
        ordering = ('nome',)

    def __str__(self):

        if self.autor_related:
            return str(self.autor_related)
        else:
            if str(self.cargo):
                return _('%(nome)s - %(cargo)s') % {
                    'nome': self.nome, 'cargo': self.cargo}
            else:
                return str(self.nome)
        """if str(self.tipo) == 'Parlamentar' and self.parlamentar:
            return self.parlamentar.nome_parlamentar
        elif str(self.tipo) == 'Comissao' and self.comissao:
            return str(self.comissao)
        elif str(self.tipo) == 'Partido' and self.partido:
            return str(self.partido)
        else:
        """


def cria_models_tipo_autor(app_config=None, verbosity=2, interactive=True,
                           using=DEFAULT_DB_ALIAS, **kwargs):

    models = models_with_gr_for_model(Autor)

    print("\n\033[93m\033[1m{}\033[0m".format(
        _('Atualizando registros TipoAutor do SAPL:')))
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        tipo_autor = TipoAutor.objects.filter(
            content_type=content_type.id).exists()

        if tipo_autor:
            msg1 = "Carga de {} não efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " Já Existe um {} {} relacionado...".format(
                TipoAutor._meta.verbose_name,
                model._meta.verbose_name)
            msg = "  {}{}".format(msg1, msg2)
        else:
            novo_autor = TipoAutor()
            novo_autor.content_type_id = content_type.id
            novo_autor.descricao = model._meta.verbose_name
            novo_autor.save()
            msg1 = "Carga de {} efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " {} {} criado...".format(
                TipoAutor._meta.verbose_name, content_type.model)
            msg = "  {}{}".format(msg1, msg2)
        print(msg)
    # Disconecta função para evitar a chamada repetidas vezes.
    post_migrate.disconnect(receiver=cria_models_tipo_autor)


post_migrate.connect(receiver=cria_models_tipo_autor)
