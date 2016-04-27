# -*- coding: utf-8 -*-
import pytest
from django.contrib.auth.models import User
from django.test.html import parse_html as html


pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user('jfirmino', password='123')


def test_login_aparece_na_barra_para_usuario_nao_logado(client):
    response = client.get('/')
    assert '<a href="/login/?next=/">Login</a>' in str(response.content)


def test_username_do_usuario_logado_aparece_na_barra(client, user):
    assert client.login(username='jfirmino', password='123')
    response = client.get('/')
    assert '<a href="/login/?next=/">Login</a>' not in str(response.content)
    assert 'jfirmino' in response.content
    assert '<a href="/logout/?next=/">Sair</a>' in str(response.content)


def test_nome_completo_do_usuario_logado_aparece_na_barra(client, user):
    # nome completo para o usuario
    user.first_name = 'Joao'
    user.last_name = 'Firmino'
    user.save()
    assert client.login(username='jfirmino', password='123')
    response = client.get('/')
    assert '<a href="/login/?next=/">Login</a>' not in str(response.content)
    assert 'Joao Firmino' in str(response.content)
    assert '<a href="/logout/?next=/">Sair</a>' in str(response.content)


# @pytest.mark.parametrize("link_login,destino", [
#     # login a partir de uma pagina retorna para ela mesma
#     ('/login/?next=/zzzz', 'http://testserver/zzzz'),
#     ('/login/?next=/', 'http://testserver/'),
#     # login a partir da propria pagina de login redireciona para home
#     ('/login/?next=/login/', 'http://testserver/'),
#     # link sem destino de retorno (next) redireciona para home
#     ('/login/', 'http://testserver/'),
# ])
# def test_login(app, user, link_login, destino):
#     pagina_login = app.get(link_login)
#     form = pagina_login.forms['login-form']
#     form['username'] = 'jfirmino'
#     form['password'] = '123'
#     res = form.submit()

#     assert user.pk == app.session['_auth_user_id']
#     assert res.url == destino


# @pytest.mark.urls('home.teststub_urls')
# @pytest.mark.parametrize("link_logout,destino", [
#     # logout a partir de uma pagina retorna para ela mesma
#     ('/logout/?next=/zzzz', 'http://testserver/zzzz'),
#     ('/logout/?next=/', 'http://testserver/'),
#     # logout a partir da propria pagina de logout redireciona para home
#     ('/logout/?next=/logout/', 'http://testserver/'),
#     # link sem destino de retorno (next) redireciona para home
#     ('/logout/', 'http://testserver/'),
# ])
# def test_logout(client, user, link_logout, destino):
#     # com um usuário logado ...
#     assert client.login(username='jfirmino', password='123')
#     assert user.pk == client.session['_auth_user_id']

#     # ... acionamos o link de logout
#     res = client.get(link_logout, follow=True)
#     destino_real = res.redirect_chain[-1][0]

#     assert '_auth_user_id' not in client.session
#     assert destino_real == destino
