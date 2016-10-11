from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
import pytest

from sapl.crud.base import PermissionRequiredForAppCrudMixin
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

btn_login = ('<input class="btn btn-success btn-sm" '
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

    # Verifica a url é de um CrudAux e, se for, testa se está
    # na página Tabelas Auxiliares
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

apps_url_patterns_prefixs_and_users = {
    'base': {
        'users': {'operador_geral': ['/sistema']},
        'prefixs': [
            '/sistema',
            '/login',
            '/logout'
        ]},
    'comissoes': {
        'users': {'operador_geral': ['/sistema', '/comissao'],
                  'operador_comissoes': ['/comissao']},
        'prefixs': [
            '/comissao',
            '/sistema'
        ]},
    'compilacao': {
        'prefixs': [
            '/ta',
        ]},
    'lexml': {
        'prefixs': [
            '/lexml',
            '/sistema'
        ]},
    'materia': {
        'users': {'operador_geral': ['/sistema', '/materia'],
                  'operador_autor': ['/proposicao'],
                  'operador_materia': ['/materia']},
        'prefixs': [
            '/materia',
            '/proposicao',
            '/sistema'
        ]},
    'norma': {
        'users': {'operador_geral': ['/sistema', '/norma'],
                  'operador_norma': ['/norma']},
        'prefixs': [
            '/norma',
            '/sistema'
        ]},
    'painel': {
        'users': {'operador_geral': ['/sistema', '/painel'],
                  'operador_painel': ['/painel']},
        'prefixs': [
            '/painel',
            '/sistema'
        ]},
    'parlamentares': {
        'users': {'operador_geral': ['/sistema',
                                     '/mesa-diretora',
                                     '/parlamentar']},
        'prefixs': [
            '/parlamentar',
            '/mesa-diretora',
            '/sistema'
        ]},
    'protocoloadm': {
        'users': {'operador_geral': ['/sistema',
                                     '/docadm',
                                     '/protocoloadm'],
                  'operador_administrativo': ['/docadm'],
                  'operador_protocoloadm': ['/protocoloadm']},
        'prefixs': [
            '/protocoloadm',
            '/docadm',
            '/sistema'
        ]},
    'relatorios': {
        'prefixs': [
            '/relatorios',
        ]},
    'sessao': {
        'users': {'operador_geral': ['/sistema', 'sessao'],
                  'operador_sessao': ['/sessao']},
        'prefixs': [
            '/sessao',
            '/sistema',
        ]},
}


@pytest.mark.parametrize('url_item', _lista_urls)
def test_urlpatterns(url_item, admin_client):

    key, url, var, app_name = url_item
    url = '/' + (url % {v: 1 for v in var})

    assert '\n' not in url, """
        A url (%s) da app (%s) está mal formada.
    """ % (app_name, url)

    app_name = app_name[5:]

    assert app_name in apps_url_patterns_prefixs_and_users, """
        A app (%s) da url (%s) não consta na lista de prefixos do teste
    """ % (app_name, url)

    if app_name in apps_url_patterns_prefixs_and_users:
        prefixs = apps_url_patterns_prefixs_and_users[app_name]['prefixs']

        isvalid = False
        for prefix in prefixs:
            if url.startswith(prefix):
                isvalid = True
                break

        assert isvalid, """
        O prefixo da url (%s) não está no padrão de sua app (%s).
        Os prefixos permitidos são:
        %s
        """ % (url, app_name, prefixs)

urls_publicas_excecoes = {
    'get': [
        '/materia/confirmar/1/1',
        '/materia/pesquisar-materia',
        '/mesa-diretora/',
        '/norma/pesquisa',
        '/sessao/1/expediente',
        '/sessao/1/mesa',
        '/sessao/1/presenca',
        '/sessao/1/presencaordemdia',
        '/sessao/1/resumo',
        '/sessao/pauta-sessao',
        '/sessao/pauta-sessao/1',
        '/sessao/pauta-sessao/pesquisar-pauta',
        '/sessao/pesquisar-sessao',
        '/sessao/1/reordenar-expediente',
        '/sessao/1/reordenar-ordem',

        '/proposicao/1/ta',  # FIXME Compilação deverá tratar
        '/materia/1/ta',
        '/norma/1/ta',

        '/comissao/1/materias-em-tramitacao',

        '/proposicao/',
        '/proposicao/1',
        '/proposicao/1/delete',
        '/proposicao/1/edit',
        '/protocoloadm/pesquisar-autor',

        '/sistema/relatorios/presenca',
        '/sistema/relatorios/materia-por-tramitacao',
        '/sistema/relatorios/materia-por-autor',
        '/sistema/relatorios/materia-por-ano-autor-tipo',
        '/sistema/relatorios/historico-tramitacoes',
        '/sistema/relatorios/atas',
        '/sistema/relatorios/',
        '/sistema/ajuda/1',
        '/sistema/ajuda/',
    ],
    'post': [
        '/norma/pesquisa-resultado',
        '/mesa-diretora/',  # tratamento de permissão interno.
        '/sessao/1/resumo',
        '/sessao/pauta-sessao',
        '/sessao/pauta-sessao/1',
        '/sessao/pauta-sessao/1/expediente/',
        '/sessao/pauta-sessao/1/ordem/',
        '/sessao/pesquisar-sessao',
        '/sessao/1/reordenar-expediente',
        '/sessao/1/reordenar-ordem',
        '/sessao/pauta-sessao/pesquisar-pauta',
        '/sessao/pesquisar-sessao',

        '/comissao/1/materias-em-tramitacao',

        '/proposicao/1/ta',
        '/materia/1/ta',
        '/norma/1/ta',
        '/materia/confirmar/1/1',
        '/materia/pesquisar-materia',

        '/proposicao/',
        '/proposicao/1',
        '/proposicao/1/delete',
        '/proposicao/1/edit',
        '/protocoloadm/pesquisar-autor',

        '/sistema/relatorios/presenca',
        '/sistema/relatorios/materia-por-tramitacao',
        '/sistema/relatorios/materia-por-autor',
        '/sistema/relatorios/materia-por-ano-autor-tipo',
        '/sistema/relatorios/historico-tramitacoes',
        '/sistema/relatorios/atas',
        '/sistema/relatorios/',
        '/sistema/ajuda/1',
        '/sistema/ajuda/',
    ]
}


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('url_item', _lista_urls)
def test_permissions_urls_for_users_by_apps(url_item, client):
    key, url, var, app_name = url_item
    url = '/' + (url % {v: 1 for v in var})

    if not get_user_model().objects.exists():
        for app in sapl_appconfs:
            # readequa permissões dos models adicionando
            # list e detail permissions
            create_perms_post_migrate(app)
        # cria usuários de perfil do sapl
        cria_grupos_permissoes()
    users = get_user_model().objects.values_list('username', flat=True)

    app_labels = app_name.split('.')[1]

    view = None
    if hasattr(key, 'view_class'):
        view = key.view_class()

        """
        A classe PermissionRequiredForAppCrudMixin pode ser usada em uma
        app mas envolver permissoes para outras
        como é o caso de PainelView que está na app 'sessao'
        mas é um redirecionamento para 'painel'... aqui é feita
        a troca da app a ser testada, por essas outras possíveis.

        Este, até a ultima versão deste teste é o único tipo de view que
            possui restrição restrição simples, por permissão, e não por
            container, como é o caso de proposições que possui restrição
            por usuário e não só por, ou não tem, o campo permission_required
        """
        if PermissionRequiredForAppCrudMixin in type.mro(key.view_class):
            # essa classe deve informar app_label
            assert hasattr(key.view_class, 'app_label')
            # app_label deve ter conteudo
            assert key.view_class.app_label
            app_labels = key.view_class.app_label
        else:

            if hasattr(view, 'permission_required') and \
                    view.permission_required is not None and\
                    len(view.permission_required) == 0:
                """
                condição do Crud, se tem permission_required e ele é igual [],
                então é uma view pública, teste liberado.
                """
                return
            else:
                """
                Views que não se encaixam nãs condições acima, podem possuir
                ou não restrição de acesso. Se o código continuar,
                será tratado como tentativa de validar pois é possível
                ter restrição local, como uma anotação method_required.
                Caberá ao desenvolvedor de uma nova view, se for pública e
                sem necessidade de nenhum tratamento de permissão, para limpar
                o teste to py.test adicionar sua url
                representativa na variavel externa ao teste:

                    urls_publicas_excecoes, logo acima do teste
                """
                pass

    if isinstance(app_labels, str):
        app_labels = app_labels,

    for app in app_labels:

        assert app in apps_url_patterns_prefixs_and_users, """
            O app_label (%s) associado a url (%s) não está na base de testes.
            %s
            """ % (app_name, url)

        if 'users' not in apps_url_patterns_prefixs_and_users[app]:
            continue

        users_for_url_atual_app = apps_url_patterns_prefixs_and_users[
            app]['users']

        for username in users:
            print(username, users_for_url_atual_app, url)

            client.login(username=username, password='interlegis')

            rg = None
            try:
                if url not in urls_publicas_excecoes['get']:
                    rg = client.get(url, {}, follow=True)
            except:
                pass

            rp = None
            try:
                if url not in urls_publicas_excecoes['post']:
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
            VIEWS BEM FORMADAS PARA VALIDAÇÃO DE ACESSO DEVEM SEMPRE
            REDIRECIONAR PARA
            LOGIN ANTES DE SUA EXECUÇÃO", desta forma nunca gerando erro
            interno dada qualquer incoerência de parâmetros nas urls
            """

            for _type, content in (
                    ('get', str(rg.content if rg else '')),
                    ('post', str(rp.content if rp else ''))):

                if not content:
                    continue

                def _assert_login(_in):
                    if _in:
                        assert btn_login in content, """
                            No teste de requisição "%s" a url (%s).
                            App (%s)
                            O usuário (%s) deveria ser redirecionado
                            para tela de login.
                            """ % (_type, url, app, username)
                    else:
                        assert btn_login not in content, """
                            No teste de requisição "%s" a url (%s).
                            App (%s)
                            O usuário (%s) não deveria ser redirecionado
                            para tela de login. Se essa é uma url
                            invariavelmente pública, a adicione na variavel
                            abaixo localizada no arquivo que se encontra este
                            teste:

                                urls_publicas_excecoes


                            """ % (_type, url, app, username)

                if username not in users_for_url_atual_app:
                    # se não é usuário da app deve ser redirecionado para login
                    _assert_login(True)
                else:
                    prefixs = users_for_url_atual_app[username]
                    for pr in prefixs:
                        if url.startswith(pr):
                            _assert_login(False)
                            break

            client.get('/logout/', follow=True)
