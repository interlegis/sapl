from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import CharField, TextField
from django.http.response import HttpResponseNotFound
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy
import pytest

from sapl.crud.base import PermissionRequiredForAppCrudMixin, CrudAux
from scripts.inicializa_grupos_autorizacoes import cria_grupos_permissoes
from scripts.lista_urls import lista_urls

from .settings import SAPL_APPS


pytestmark = pytest.mark.django_db

sapl_appconfs = [apps.get_app_config(n[5:]) for n in SAPL_APPS]
_lista_urls = lista_urls()


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


def test_charfield_textfield():
    for app in sapl_appconfs:
        for model in app.get_models():
            fields = model._meta.local_fields
            for field in fields:
                if isinstance(field, (CharField, TextField)):
                    assert not field.null, 'This %s is null: %s.%s' % (
                        type(field).__name__,
                        model.__name__,
                        field.attname)


def test_str_sanity():
    # this simply a sanity check
    # __str__ semantics is not considered and should be tested separetely
    for app in sapl_appconfs:
        for model in app.get_models():
            obj = mommy.prepare(model)
            try:
                str(obj)
            except Exception as exc:
                msg = '%s.%s.__str__ is broken.' % (
                    model.__module__, model.__name__)
                raise AssertionError(msg, exc)

btn_login = ('<input class="btn btn-success btn-sm" ' +
             'type="submit" value="login" />')


@pytest.mark.parametrize('url_item', _lista_urls)
def test_crudaux_formato_inicio_urls_associadas(url_item):

    # Verifica se um crud é do tipo CrudAux, se sim, sua url deve começar
    # com /sistema/
    key, url, var, app_name = url_item
    url = '/' + (url % {v: 1 for v in var})

    view_class = None
    if hasattr(key, 'view_class'):
        view_class = key.view_class

    # se não tem view_class, possivelmente é não é uma classed base view
    if not view_class:
        return

    # se não tem atributo crud, não é será nenhum tipo de crud
    if not hasattr(view_class, 'crud'):
        return

    # se o crud da view_class relativa a url a ser testada,
    # implementa a classe CrudAux, seu link deve iniciar com /sistema
    for string_class in list(map(str, type.mro(view_class.crud))):

        if 'CrudAux' in string_class:
            assert url.startswith('/sistema'), """
                        A url (%s) foi gerada a partir de um CrudAux,
                        o que diz que está é uma implementação de uma
                        tabela auxiliar, porém a url em questão, está fora
                        do padrão, que é iniciar com /sistema.
                    """ % (url)


@pytest.mark.parametrize('url_item', _lista_urls)
def test_crudaux_list_do_crud_esta_na_pagina_sistema(url_item, admin_client):

    # Verifica se um crud é do tipo CrudAux, se sim, sua url deve começar
    # com /sistema/
    key, url, var, app_name = url_item
    url = '/' + (url % {v: 1 for v in var})

    view_class = None
    if hasattr(key, 'view_class'):
        view_class = key.view_class

    # se não tem view_class, possivelmente não é uma classed base view
    if not view_class:
        return

    # se não tem atributo crud, não é será nenhum tipo de crud
    if not hasattr(view_class, 'crud'):
        return

    herancas_crud = list(map(str, type.mro(view_class.crud)))
    for string_class in herancas_crud:
        if 'CrudAux' in string_class:

            herancas_view = list(map(str, type.mro(view_class)))

            for string_view_class in herancas_view:
                # verifica se o link para manutenção do crud está em /sistema
                if 'ListView' in string_view_class:
                    response = admin_client.get('/sistema', {}, follow=True)
                    assert url in str(response.content), """
                        A url (%s) não consta nas Tabelas Auxiliares, 
                        porem é uma implementação de ListView de CrudAux.
                        Se encontra em %s.urls
                    """ % (url, app_name)


@pytest.mark.parametrize('urls_app', _lista_urls)
def em_construcao_crud_permissions_urls(urls_app, client):
    if not get_user_model().objects.exists():
        for app in sapl_appconfs:
            # readequa permissões dos models adicionando
            # list e detail permissions
            create_perms_post_migrate(app)
        # cria usuários de perfil do sapl
        cria_grupos_permissoes()
    users = get_user_model().objects.values_list('username', flat=True)

    for url_item in _lista_urls[urls_app]:

        key, url, var, app_name = url_item
        url = '/' + (url % {v: 1 for v in var})

        app_labels = app_name.split('.')[1]

        view_class = None
        if hasattr(key, 'view_class'):
            view_class = key.view_class

            """
            A classe PermissionRequiredForAppCrudMixin pode ser usada em uma
            app mas envolver permissoes para outras 
            como é o caso de PainelView que está na app 'sessao'
            mas é um redirecionamento para 'painel'... aqui é feita
            a troca a urls_app a ser testada, por essas outras possíveis
            """
            if PermissionRequiredForAppCrudMixin in type.mro(view_class):
                # essa classe deve informar app_label
                assert hasattr(view_class, 'app_label')
                # app_label deve ter conteudo
                assert view_class.app_label
                app_labels = view_class.app_label

        if isinstance(app_labels, str):
            app_labels = app_labels,

        for app in app_labels:

            # monta o username correspondente de a app da url a ser testada
            user_for_url_atual_app = 'operador_%s'
            if app in ['base', 'parlamentares']:
                user_for_url_atual_app = user_for_url_atual_app % 'geral'
            elif app in 'protocoloadm':
                user_for_url_atual_app = user_for_url_atual_app % 'administrativo'
            elif app in ['compilacao']:
                return  # TODO implementar teste para compilacao
            else:
                user_for_url_atual_app = user_for_url_atual_app % app

            for username in users:
                print(username, user_for_url_atual_app, url)

                client.login(username=username, password='interlegis')

                rg = None
                try:
                    rg = client.get(url, {}, follow=True)
                except:
                    pass

                rp = None
                try:
                    rp = client.post(url, {}, follow=True)
                except:
                    pass

                """
                devido às urls serem incompletas ou com pks e outras valores
                inexistentes na base, iniciar a execução da view, seja por get,
                post ou qualquer outro método pode causar o erro...
                por isso o "try ... except" acima.
                No entanto, o objetivo do teste é validar o acesso de toda url.
                Independente do erro que vá acontecer, esse erro não ocorrerá
                se o user não tiver permissão de acesso pelo fato de que "AS
                VIEWS BEM FORMADAS PARA VALIDAÇÃO DE ACESSO DEVEM SEMPRE REDIRECIONAR PARA
                LOGIN ANTES DE SUA EXECUÇÃO", desta forma nunca gerando erro
                interno dada qualquer incoerência de parâmetros nas urls
                """
                if rg:
                    """
                    Se o usuário a ser testado é o usuário da app da url de get
                    espera-se que não tenha recebido uma tela de login
                    """
                    if username == user_for_url_atual_app and\
                            not url.startswith('/sistema/'):
                        assert btn_login not in str(rg.content)
                    elif username != 'operador_geral' and\
                            url.startswith('/sistema/'):
                        assert btn_login in str(rg.content)
                    elif username == 'operador_geral' and\
                            url.startswith('/sistema/'):
                        assert btn_login not in str(rg.content)

                if rp:
                    """
                    Se o usuário a ser testado é o usuário da app da url de
                    post espera-se que não tenha recebido uma tela de login
                    """
                    if username == user_for_url_atual_app and\
                            not url.startswith('/sistema/'):
                        assert btn_login not in str(rp.content)
                    elif username != 'operador_geral' and\
                            url.startswith('/sistema/'):
                        assert btn_login in str(rp.content)
                    elif username == 'operador_geral' and\
                            url.startswith('/sistema/'):
                        assert btn_login not in str(rp.content)

                logout = client.get('/logout/', follow=True)
