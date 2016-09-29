from builtins import LookupError

from django.apps import apps
from django.contrib.auth.management import _get_all_permissions
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import exceptions
from django.db import models, router
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat

from sapl.utils import UF, YES_NO_CHOICES

TIPO_DOCUMENTO_ADMINISTRATIVO = (('O', _('Ostensivo')),
                                 ('R', _('Restritivo')))

SEQUENCIA_NUMERACAO = (('A', _('Sequencial por ano')),
                       ('U', _('Sequencial único')))


def get_sessao_media_path(instance, subpath, filename):
    return './sapl/casa/%s/%s' % (subpath, filename)


def get_casa_media_path(instance, filename):
    return get_sessao_media_path(instance, 'Logotipo', filename)


class CasaLegislativa(models.Model):
    # TODO ajustar todos os max_length !!!!
    # cod_casa => id (pk)

    codigo = models.CharField(max_length=100, verbose_name=_('Codigo'))
    nome = models.CharField(max_length=100, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=100, verbose_name=_('Sigla'))
    endereco = models.CharField(max_length=100, verbose_name=_('Endereço'))
    cep = models.CharField(max_length=100, verbose_name=_('CEP'))
    municipio = models.CharField(max_length=100, verbose_name=_('Município'))
    uf = models.CharField(max_length=100,
                          choices=UF,
                          verbose_name=_('UF'))
    telefone = models.CharField(
        max_length=100, blank=True, verbose_name=_('Telefone'))
    fax = models.CharField(
        max_length=100, blank=True, verbose_name=_('Fax'))
    logotipo = models.ImageField(
        blank=True,
        upload_to=get_casa_media_path,
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


class ProblemaMigracao(models.Model):
    content_type = models.ForeignKey(ContentType,
                                     verbose_name=_('Tipo de Content'))
    object_id = models.PositiveIntegerField(verbose_name=_('ID do Objeto'))
    content_object = GenericForeignKey('content_type', 'object_id')
    nome_campo = models.CharField(max_length=100,
                                  blank=True,
                                  verbose_name='Nome do(s) Campo(s)')
    problema = models.CharField(max_length=300, verbose_name=_('Problema'))
    descricao = models.CharField(max_length=300, verbose_name=_('Descrição'))
    eh_stub = models.BooleanField(verbose_name='É stub?')

    class Meta:
        verbose_name = _('Problema na Migração')
        verbose_name_plural = _('Problemas na Migração')


class AppConfig(models.Model):
    documentos_administrativos = models.CharField(
        max_length=1,
        verbose_name=_('Ostensivo/Restritivo'),
        choices=TIPO_DOCUMENTO_ADMINISTRATIVO, default='O')

    sequencia_numeracao = models.CharField(
        max_length=1,
        verbose_name=_('Sequência de numeração'),
        choices=SEQUENCIA_NUMERACAO, default='A')

    painel_aberto = models.BooleanField(
        verbose_name=_('Painel aberto para usuário anônimo'),
        choices=YES_NO_CHOICES, default=False)

    class Meta:
        verbose_name = _('Configurações da Aplicação')
        verbose_name_plural = _('Configurações da Aplicação')
        permissions = (
            ('menu_sistemas', _('Renderizar Menu Sistemas')),
            ('view_tabelas_auxiliares', _('Visualizar Tabelas Auxiliares')),
        )

    def __str__(self):
        return _('Configurações da Aplicação - %(id)s') % {
            'id': self.id}


def create_proxy_permissions(
        app_config, verbosity=2, interactive=True,
        using=DEFAULT_DB_ALIAS, **kwargs):
    if not app_config.models_module:
        return

    # print(app_config)

    try:
        Permission = apps.get_model('auth', 'Permission')
    except LookupError:
        return

    if not router.allow_migrate_model(using, Permission):
        return

    from django.contrib.contenttypes.models import ContentType

    permission_name_max_length = Permission._meta.get_field('name').max_length

    # This will hold the permissions we're looking for as
    # (content_type, (codename, name))
    searched_perms = list()
    # The codenames and ctypes that should exist.
    ctypes = set()
    for klass in list(app_config.get_models()):
        opts = klass._meta
        permissions = (
            ("list_" + opts.model_name,
             string_concat(
                 _('Visualizaçao da lista de'), ' ',
                 opts.verbose_name_plural)),
            ("detail_" + opts.model_name,
             string_concat(
                 _('Visualização dos detalhes de'), ' ',
                 opts.verbose_name_plural)),
        )
        opts.permissions = tuple(
            set(list(permissions) + list(opts.permissions)))

        if opts.proxy:
            # Force looking up the content types in the current database
            # before creating foreign keys to them.
            app_label, model = opts.app_label, opts.model_name

            try:
                ctype = ContentType.objects.db_manager(
                    using).get_by_natural_key(app_label, model)
            except:
                ctype = ContentType.objects.db_manager(
                    using).create(app_label=app_label, model=model)
        else:
            ctype = ContentType.objects.db_manager(using).get_for_model(klass)

        ctypes.add(ctype)
        for perm in _get_all_permissions(klass._meta, ctype):
            searched_perms.append((ctype, perm))

    # Find all the Permissions that have a content_type for a model we're
    # looking for.  We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set(Permission.objects.using(using).filter(
        content_type__in=ctypes,
    ).values_list(
        "content_type", "codename"
    ))

    perms = [
        Permission(codename=codename, name=name, content_type=ct)
        for ct, (codename, name) in searched_perms
        if (ct.pk, codename) not in all_perms
    ]
    # Validate the permissions before bulk_creation to avoid cryptic database
    # error when the name is longer than 255 characters
    for perm in perms:
        if len(perm.name) > permission_name_max_length:
            raise exceptions.ValidationError(
                'The permission name %s of %s.%s '
                'is longer than %s characters' % (
                    perm.name,
                    perm.content_type.app_label,
                    perm.content_type.model,
                    permission_name_max_length,
                )
            )
    Permission.objects.using(using).bulk_create(perms)
    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '%s'" % perm)


models.signals.post_migrate.connect(
    receiver=create_proxy_permissions,
    dispatch_uid="django.contrib.auth.management.create_permissions")
