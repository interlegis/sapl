from builtins import LookupError

import django
import reversion
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.management import _get_all_permissions
from django.core import exceptions
from django.db import models, router
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat

from sapl.rules import (SAPL_GROUP_ADMINISTRATIVO, SAPL_GROUP_COMISSOES,
                        SAPL_GROUP_GERAL, SAPL_GROUP_MATERIA, SAPL_GROUP_NORMA,
                        SAPL_GROUP_PAINEL, SAPL_GROUP_PROTOCOLO,
                        SAPL_GROUP_SESSAO)


class AppConfig(django.apps.AppConfig):
    name = 'sapl.rules'
    label = 'rules'
    verbose_name = _('Regras de Acesso')


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

        # FIXME: Retirar try except quando sapl passar a usar django 1.11
        try:
            # Função não existe mais em Django 1.11
            # como sapl ainda não foi para Django 1.11
            # esta excessão foi adicionada para caso o
            # Sapl esteja rodando em um projeto 1.11 não ocorra erros
            _all_perms_of_klass = _get_all_permissions(klass._meta, ctype)
        except:
            # Nova função usada em projetos com Django 1.11 e o sapl é uma app
            _all_perms_of_klass = _get_all_permissions(klass._meta)

        for perm in _all_perms_of_klass:
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


def get_rules():

    from sapl.rules.map_rules import rules_patterns
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    class Rules:

        def __init__(self, rules_patterns):
            self.rules_patterns = rules_patterns

        def associar(self, g, model, tipo):
            for t in tipo:
                content_type = ContentType.objects.get_by_natural_key(
                    app_label=model._meta.app_label,
                    model=model._meta.model_name)

                codename = (t[1:] + model._meta.model_name)\
                    if t[0] == '.' and t[-1] == '_' else t

                p = Permission.objects.get(
                    content_type=content_type,
                    codename=codename)
                g.permissions.add(p)
            g.save()

        def _config_group(self, group_name, rules_list):
            if not group_name:
                return

            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()

            try:
                print(' ', group_name)
                for model, perms in rules_list:
                    self.associar(group, model, perms)
            except Exception as e:
                print(group_name, e)

        def groups_add_user(self, user, groups_name):
            if not isinstance(groups_name, list):
                groups_name = [groups_name, ]
            for group_name in groups_name:
                if not group_name or user.groups.filter(
                        name=group_name).exists():
                    continue
                g = Group.objects.get_or_create(name=group_name)[0]
                user.groups.add(g)

        def groups_remove_user(self, user, groups_name):
            if not isinstance(groups_name, list):
                groups_name = [groups_name, ]
            for group_name in groups_name:
                if not group_name or not user.groups.filter(
                        name=group_name).exists():
                    continue
                g = Group.objects.get_or_create(name=group_name)[0]
                user.groups.remove(g)

        def cria_usuario(self, nome, grupo):
            nome_usuario = nome
            param_username = {get_user_model().USERNAME_FIELD: nome_usuario}
            usuario = get_user_model().objects.get_or_create(
                **param_username)[0]
            usuario.set_password('interlegis')
            usuario.save()
            g = Group.objects.get_or_create(name=grupo)[0]
            g.user_set.add(usuario)

        def cria_usuarios_padrao(self):
            for group, user in (
                (SAPL_GROUP_ADMINISTRATIVO, 'operador_administrativo'),
                (SAPL_GROUP_PROTOCOLO, 'operador_protocoloadm'),
                (SAPL_GROUP_COMISSOES, 'operador_comissoes'),
                (SAPL_GROUP_MATERIA, 'operador_materia'),
                (SAPL_GROUP_NORMA, 'operador_norma'),
                (SAPL_GROUP_SESSAO, 'operador_sessao'),
                (SAPL_GROUP_PAINEL, 'operador_painel'),
                (SAPL_GROUP_GERAL, 'operador_geral'),
            ):
                self.cria_usuario(user, group)

        def update_groups(self):
            print('')
            print(string_concat('\033[93m\033[1m',
                                _('Atualizando grupos do SAPL:'),
                                '\033[0m'))
            for rules_group in self.rules_patterns:
                group_name = rules_group['group']
                rules_list = rules_group['rules']
                self._config_group(group_name, rules_list)

    return Rules(rules_patterns)


def update_groups(app_config, verbosity=2, interactive=True,
                  using=DEFAULT_DB_ALIAS, **kwargs):

    if app_config != AppConfig and not isinstance(app_config, AppConfig):
        return

    rules = get_rules()
    rules.update_groups()


def cria_usuarios_padrao():
    rules = get_rules()
    rules.cria_usuarios_padrao()


def revision_pre_delete_signal(sender, **kwargs):
    with reversion.create_revision():
        kwargs['instance'].save()
        reversion.set_comment("Deletado pelo sinal.")


models.signals.post_migrate.connect(
    receiver=update_groups)


models.signals.post_migrate.connect(
    receiver=create_proxy_permissions,
    dispatch_uid="django.contrib.auth.management.create_permissions")

models.signals.pre_delete.connect(
    receiver=revision_pre_delete_signal,
    dispatch_uid="pre_delete_signal")
