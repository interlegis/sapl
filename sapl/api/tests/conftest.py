import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient


def resultados(response):
    """Lista de objetos de uma resposta da API, paginada ou não."""
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    return data


def ids(response):
    return {obj['id'] for obj in resultados(response)}


@pytest.fixture
def usuario(db):
    """Cria um usuário com as permissões informadas ('app_label.codename')."""
    def _usuario(username, *perms, **kwargs):
        user = get_user_model().objects.create_user(
            username=username, password='senha-de-teste', **kwargs)
        for perm in perms:
            app_label, codename = perm.split('.')
            user.user_permissions.add(Permission.objects.get(
                content_type__app_label=app_label, codename=codename))
        return user
    return _usuario


@pytest.fixture
def api():
    """Cliente da API anônimo ou autenticado por sessão."""
    def _api(user=None):
        client = APIClient()
        if user is not None:
            client.force_login(user)
        return client
    return _api
