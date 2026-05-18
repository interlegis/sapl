# -*- coding: utf-8 -*-
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import override_settings
import pytest

from sapl.base.govbr import GOVBR_SESSION_KEY, resolve_user


pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return get_user_model().objects.create_user('jfirmino', password='123')


def test_login_aparece_na_barra_para_usuario_nao_logado(client):
    response = client.get('/')
    assert '<a class="nav-link" href="/login/"><img src="/static/sapl/frontend/img/user.png"></a>' in str(
        response.content)


def test_username_do_usuario_logado_aparece_na_barra(client, user):
    assert client.login(username='jfirmino', password='123')
    response = client.get('/')
    assert '<a class="nav-link" href="/login/">Login</a>' not in str(
        response.content)
    assert 'jfirmino' in str(response.content)
    assert '<a href="/logout/">Sair</a>' in str(response.content)


@override_settings(GOVBR_LOGIN_ENABLED=False)
def test_botao_govbr_nao_aparece_por_padrao(client):
    response = client.get('/login/')

    assert 'Entrar com GOV.BR' not in str(response.content)


@override_settings(GOVBR_LOGIN_ENABLED=True)
def test_botao_govbr_aparece_quando_habilitado(client):
    response = client.get('/login/')

    assert 'Entrar com GOV.BR' in str(response.content)


@override_settings(
    GOVBR_LOGIN_ENABLED=True,
    GOVBR_CLIENT_ID='cliente-sapl',
    GOVBR_CLIENT_SECRET='segredo',
    GOVBR_SSO_BASE_URL='https://sso.staging.acesso.gov.br',
    GOVBR_SCOPE='openid email profile govbr_confiabilidades govbr_confiabilidades_idtoken',
    GOVBR_REDIRECT_URI='https://sapl.indaiatuba.tec.br/auth/govbr/callback/')
def test_inicio_login_govbr_redireciona_para_authorize(client):
    response = client.get('/login/govbr/?next=/sistema/')
    redirect = urlparse(response['Location'])
    params = parse_qs(redirect.query)

    assert response.status_code == 302
    assert redirect.scheme == 'https'
    assert redirect.netloc == 'sso.staging.acesso.gov.br'
    assert redirect.path == '/authorize'
    assert params['response_type'] == ['code']
    assert params['client_id'] == ['cliente-sapl']
    assert params['redirect_uri'] == [
        'https://sapl.indaiatuba.tec.br/auth/govbr/callback/']
    assert params['code_challenge_method'] == ['S256']
    assert params['state'] == [client.session[GOVBR_SESSION_KEY]['state']]
    assert client.session[GOVBR_SESSION_KEY]['next'] == '/sistema/'


@override_settings(GOVBR_USER_LOOKUP_FIELDS='username')
def test_resolve_usuario_govbr_por_cpf_no_username(user):
    user.username = '12345678900'
    user.save()

    usuario, cpf = resolve_user(
        {'sub': '12345678900', 'preferred_username': '12345678900'},
        {'sub': '12345678900'})

    assert usuario == user
    assert cpf == '12345678900'


# def test_nome_completo_do_usuario_logado_aparece_na_barra(client, user):
#     # nome completo para o usuario
#     user.first_name = 'Joao'
#     user.last_name = 'Firmino'
#     user.save()
#     assert client.login(username='jfirmino', password='123')
#     response = client.get('/')
#     assert '<a href="/login/">Login</a>' not in str(response.content)
#     assert 'Joao Firmino' in str(response.content)
#     assert '<a href="/logout/">Sair</a>' in str(response.content)


@pytest.mark.urls('sapl.base.tests.teststub_urls')
@pytest.mark.parametrize("link_login,destino", [
    # login redireciona para home
    ('/login/', '/'),
])
def test_login(app, user, link_login, destino):
    pagina_login = app.get(link_login)
    form = pagina_login.forms['login-form']
    form['username'] = 'jfirmino'
    form['password'] = '123'
    res = form.submit()  # login

    assert str(user.pk) == app.session['_auth_user_id']
    assert res.url == destino


@pytest.mark.parametrize("link_logout,destino", [
    # logout redireciona para a pagina de login
    ('/logout/', '/login/'),
])
def test_logout(client, user, link_logout, destino):
    # com um usuário logado ...
    assert client.login(username='jfirmino', password='123')
    assert str(user.pk) == client.session['_auth_user_id']

    # ... acionamos o link de logout
    res = client.get(link_logout, follow=True)

    destino_real = res.redirect_chain[-1][0]

    assert '_auth_user_id' not in client.session
    assert destino_real == destino
