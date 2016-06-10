# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
import pytest


pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return get_user_model().objects.create_user('jfirmino', password='123')


def test_login_aparece_na_barra_para_usuario_nao_logado(client):
    response = client.get('/')
    assert '<a href="/login/">Login</a>' in str(response.content)


def test_username_do_usuario_logado_aparece_na_barra(client, user):
    assert client.login(username='jfirmino', password='123')
    response = client.get('/')
    assert '<a href="/login/">Login</a>' not in str(response.content)
    assert 'jfirmino' in str(response.content)
    assert '<a href="/logout/">Sair</a>' in str(response.content)


def test_nome_completo_do_usuario_logado_aparece_na_barra(client, user):
    # nome completo para o usuario
    user.first_name = 'Joao'
    user.last_name = 'Firmino'
    user.save()
    assert client.login(username='jfirmino', password='123')
    response = client.get('/')
    assert '<a href="/login/">Login</a>' not in str(response.content)
    assert 'Joao Firmino' in str(response.content)
    assert '<a href="/logout/">Sair</a>' in str(response.content)


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
