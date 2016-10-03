import pytest
from django.apps import apps
from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat

from inicializa_grupos_autorizacoes import cria_grupos_permissoes

pytestmark = pytest.mark.django_db

apps_com_permissao_padrao = [
    'comissoes', 'norma', 'sessao', 'painel']


def create_perms_post_migrate(app):

    searched_perms = list()
    # The codenames and ctypes that should exist.
    ctypes = set()

    for klass in list(app.get_models()):
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
                ctype = ContentType.objects.get_by_natural_key(
                    app_label, model)
            except:
                ctype = ContentType.objects.create(
                    app_label=app_label, model=model)
        else:
            ctype = ContentType.objects.get_for_model(klass)

        ctypes.add(ctype)
        for perm in _get_all_permissions(klass._meta, ctype):
            searched_perms.append((ctype, perm))

    all_perms = set(Permission.objects.filter(
        content_type__in=ctypes,
    ).values_list(
        "content_type", "codename"
    ))

    perms = [
        Permission(codename=codename, name=name, content_type=ct)
        for ct, (codename, name) in searched_perms
        if (ct.pk, codename) not in all_perms
    ]
    Permission.objects.bulk_create(perms)


@pytest.mark.parametrize('app_label', apps_com_permissao_padrao)
def test_grupo_padrao_tem_permissoes_sobre_todo_o_app(app_label):

    app = apps.get_app_config(app_label)

    create_perms_post_migrate(app)

    # código testado
    cria_grupos_permissoes()

    def gerar_permissoes(app):
        for model in app.get_models():
            for op in ['add', 'change', 'delete', ]:
                yield model, 'Can %s %s' % (op, model._meta.verbose_name)
            yield model, force_text(string_concat(
                _('Visualizaçao da lista de'), ' ',
                model._meta.verbose_name_plural))
            yield model, force_text(string_concat(
                _('Visualização dos detalhes de'),
                ' ',
                model._meta.verbose_name_plural))
    grupo = Group.objects.get(name='Operador de %s' % app.verbose_name)
    esperado = set(gerar_permissoes(app))

    real = set((p.content_type.model_class(), p.name)
               for p in grupo.permissions.all())
    assert real == esperado


@pytest.mark.parametrize('app_label', apps_com_permissao_padrao)
def test_permissoes_extras_sao_apagadas(app_label):

    app = apps.get_app_config(app_label)

    # create_perms_post_migrate(app)

    grupo = Group.objects.create(name='Operador de %s' % app.verbose_name)

    permissao_errada = Permission.objects.create(
        name='STUB', content_type=ContentType.objects.first())
    grupo.permissions.add(permissao_errada)

    # código testado
    cria_grupos_permissoes()

    assert not grupo.permissions.filter(id=permissao_errada.id).exists()
