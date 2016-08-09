import pytest
from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from inicializa_grupos_autorizacoes import cria_grupos_permissoes

pytestmark = pytest.mark.django_db

apps_com_permissao_padrao = [
    'comissoes', 'norma', 'sessao', 'painel']


@pytest.mark.parametrize('app_label', apps_com_permissao_padrao)
def test_grupo_padrao_tem_permissoes_sobre_todo_o_app(app_label):

    app = apps.get_app_config(app_label)

    # código testado
    cria_grupos_permissoes()

    def gerar_permissoes(app):
        for model in app.get_models():
            for op in ['add', 'change', 'delete']:
                yield model, 'Can %s %s' % (op, model._meta.verbose_name)
    grupo = Group.objects.get(name='Operador de %s' % app.verbose_name)
    esperado = set(gerar_permissoes(app))

    real = set((p.content_type.model_class(), p.name)
               for p in grupo.permissions.all())
    assert real == esperado


@pytest.mark.parametrize('app_label', apps_com_permissao_padrao)
def test_permissoes_extras_sao_apagadas(app_label):

    app = apps.get_app_config(app_label)
    grupo = Group.objects.create(name='Operador de %s' % app.verbose_name)

    permissao_errada = Permission.objects.create(
        name='STUB', content_type=ContentType.objects.first())
    grupo.permissions.add(permissao_errada)

    # código testado
    cria_grupos_permissoes()

    assert not grupo.permissions.filter(id=permissao_errada.id).exists()


# Operador de Comissões
# Operador de Matéria
# Operador de Norma Jurídica
# Operador de Sessão Plenária

# Operador de Protocolo Administrativo
# Operador de Documento Administrativo


# Operador Geral
