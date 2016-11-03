import pytest
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import CasaLegislativa, ProblemaMigracao
from sapl.compilacao.models import (PerfilEstruturalTextoArticulado,
                                    TipoDispositivo,
                                    TipoDispositivoRelationship)
from sapl.materia.models import AcompanhamentoMateria
from sapl.rules import SAPL_GROUPS, map_rules
from sapl.test_urls import create_perms_post_migrate
from scripts.lista_permissions_in_decorators import \
    lista_permissions_in_decorators
from scripts.lista_urls import lista_urls

sapl_appconfs = [apps.get_app_config(n[5:]) for n in settings.SAPL_APPS]

sapl_models = []
for app in sapl_appconfs:
    sapl_models.extend(app.get_models())
sapl_models.reverse()


@pytest.mark.parametrize('group_item', SAPL_GROUPS)
def test_groups_in_rules_patterns(group_item):

    test = False
    for rules_group in map_rules.rules_patterns:
        if rules_group['group'] == group_item:
            test = True

    assert test, _('O grupo (%s) não foi a rules_patterns.') % (group_item)


@pytest.mark.parametrize('model_item', sapl_models)
def test_models_in_rules_patterns(model_item):

    test = False
    for rules_group in map_rules.rules_patterns:
        rules_model = rules_group['rules']
        for rm in rules_model:
            if rm[0] == model_item:
                test = True
                break

    assert test, _('O model %s (%s) não foi adicionado em nenhum '
                   'grupo padrão para regras de acesso.') % (
                       str(model_item),
                       model_item._meta.verbose_name)

# __falsos_positivos__
__fp__in__test_permission_of_models_in_rules_patterns = {
    map_rules.RP_ADD: [CasaLegislativa,
                       ProblemaMigracao,
                       TipoDispositivo,
                       TipoDispositivoRelationship,
                       PerfilEstruturalTextoArticulado],

    map_rules.RP_CHANGE: [ProblemaMigracao,
                          AcompanhamentoMateria,
                          TipoDispositivo,
                          TipoDispositivoRelationship,
                          PerfilEstruturalTextoArticulado],

    map_rules.RP_DELETE: [CasaLegislativa,
                          ProblemaMigracao,
                          TipoDispositivo,
                          TipoDispositivoRelationship,
                          PerfilEstruturalTextoArticulado],

    map_rules.RP_LIST: [ProblemaMigracao,
                        AcompanhamentoMateria,
                        TipoDispositivo,
                        TipoDispositivoRelationship,
                        PerfilEstruturalTextoArticulado],

    map_rules.RP_DETAIL: [ProblemaMigracao,
                          AcompanhamentoMateria,
                          TipoDispositivo,
                          TipoDispositivoRelationship,
                          PerfilEstruturalTextoArticulado]

}


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('model_item', sapl_models)
def test_permission_of_models_in_rules_patterns(model_item):

    create_perms_post_migrate(model_item._meta.app_config)
    permissions = map_rules.__base__ + list(
        filter(
            lambda perm: not perm.startswith(
                'detail_') and not perm.startswith('list_'),
            map(lambda x: x[0],
                model_item._meta.permissions))
    )

    __fp__ = __fp__in__test_permission_of_models_in_rules_patterns
    for perm in permissions:
        if perm in __fp__ and model_item in __fp__[perm]:
            continue

        test = False
        for rules_group in map_rules.rules_patterns:
            rules_model = rules_group['rules']
            for rm in rules_model:
                model = rm[0]
                rules = rm[1]
                if model == model_item:
                    if perm in rules:
                        test = True
                        break

        assert test, _('A permissão (%s) do model (%s) não foi adicionado em '
                       'nenhum grupo padrão para regras de acesso.') % (
                           perm,
                           str(model_item))


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('model_item', sapl_models)
def test_permission_of_rules_exists(model_item):

    print(model_item)
    create_perms_post_migrate(model_item._meta.app_config)

    for rules_group in map_rules.rules_patterns:
        rules_model = rules_group['rules']
        for rm in rules_model:
            model = rm[0]
            rules = rm[1]

            if model != model_item:
                continue

            for r in rules:
                content_type = ContentType.objects.get_by_natural_key(
                    app_label=model._meta.app_label,
                    model=model._meta.model_name)

                codename = (r[1:] + model._meta.model_name)\
                    if r[0] == '.' and r[-1] == '_' else r
                p = Permission.objects.filter(
                    content_type=content_type,
                    codename=codename).exists()

                assert p, _('Permissão (%s) associada ao model (%s) '
                            'não está em _meta.permissions.') % (
                    codename,
                    model_item)


_lista_urls = lista_urls()


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('url_item', _lista_urls)
def test_permission_required_of_views_exists(url_item):
    """
    testa se, nas views que possuem atributo permission_required,
    as permissões fixas escritas manualmente realmente exitem em Permission

    Obs: isso não testa permissões escritas em anotações de método ou classe
    """

    for app in sapl_appconfs:
        # readequa permissões dos models adicionando
        # list e detail permissions
        create_perms_post_migrate(app)

    key, url, var, app_name = url_item
    url = '/' + (url % {v: 1 for v in var})

    assert '\n' not in url, """
        A url (%s) da app (%s) está mal formada.
    """ % (app_name, url)

    view = None
    if hasattr(key, 'view_class'):
        view = key.view_class

        if hasattr(view, 'permission_required'):
            if isinstance(view.permission_required, six.string_types):
                perms = (view.permission_required, )
            else:
                perms = view.permission_required

            if not perms:
                return

            for perm in perms:
                if perm[0] == '.' and perm[-1] == '_':
                    model = None
                    if hasattr(view, 'model') and view.model:
                        model = view.model
                    elif hasattr(view, 'filterset_class'):
                        model = view.fielterset_class._meta.model
                    elif hasattr(view, 'form_class'):
                        model = view.form_class._meta.model

                    assert model, _('model %s não localizado em %s'
                                    ) % (model, view)

                    codename = perm[1:] + view.model._meta.model_name
                else:
                    codename = perm

                codename = codename.split('.')

                if len(codename) == 1:
                    content_type = ContentType.objects.get_by_natural_key(
                        app_label=model._meta.app_label,
                        model=model._meta.model_name)
                    p = Permission.objects.filter(
                        content_type=content_type,
                        codename=codename[0]).exists()
                elif len(codename) == 2:
                    p = Permission.objects.filter(
                        content_type__app_label=codename[0],
                        codename=codename[1]).exists()

                assert p, _('Permissão (%s) na view (%s) não existe.') % (
                    codename,
                    view)


_lista_permissions_in_decorators = lista_permissions_in_decorators()


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('permission', _lista_permissions_in_decorators)
def test_permission_required_of_decorators(permission):
    """
    testa se, nos decorators permission_required com ou sem method_decorator
    as permissões fixas escritas manualmente realmente exitem em Permission
    """

    for app in sapl_appconfs:
        # readequa permissões dos models adicionando
        # list e detail permissions
        create_perms_post_migrate(app)

    codename = permission[0].split('.')
    p = Permission.objects.filter(
        content_type__app_label=codename[0],
        codename=codename[1]).exists()

    assert p, _('Permissão (%s) na view (%s) não existe.') % (
        permission[0],
        permission[1])
