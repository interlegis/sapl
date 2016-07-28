from django.apps import apps
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from sapl.settings import SAPL_APPS


def cria_grupo_e_usuario_padrao(nome_grupo, nome_usuario, permissoes):

('Operador de Sessão', )


def cria_grupos_permissoes():

    nomes_apps = ['base', 'parlamentares', 'comissoes',
                  'materia', 'norma', 'sessao', 'painel']
    permissoes = {app: list(Permission.objects.filter(
        content_type__in=ContentType.objects.filter(app_label=app)))
        for app in nomes_apps}

    # permissoes específicas para protocolo e documento administrativo
    cts = ContentType.objects.filter(app_label='protocoloadm')
    permissoes['documento_administrativo'] = list(
        Permission.objects.filter(content_type__in=cts))

    cts = cts.exclude(model__icontains='tramitacao').exclude(
        model__icontains='documentoadministrativo')
    permissoes['protocoloadm'] = list(
        Permission.objects.filter(content_type__in=cts))
    nomes_apps.append('protocoloadm')

    for nome_app in nomes_apps:

        if nome_app in {'base', 'parlamentares'}:
            # pula apps que não têm grupo específico
            continue

        nome_grupo = 'Operador de %s' % apps.get_app_config(
            nome_app).verbose_name
        grupo = Group.objects.get_or_create(name=nome_grupo)[0]

        # configura permissoes do operador
        for p in permissoes[nome_app]:
            grupo.permissions.add(p)

        nome_usuario = 'operador_%s' % nome_app

        usuario = User.objects.get_or_create(username=nome_usuario)[0]
        usuario.set_password('interlegis')
        usuario.save()
        grupo.user_set.add(usuario)

    # Operador Geral
    grupo_geral = Group.objects.get_or_create(name='Operador Geral')[0]
    for lista in permissoes.values():
        for p in lista:
            grupo_geral.permissions.add(p)

    # Autor
    # .....
    perms_autor = Permission.objects.get(name='Can add Proposição')
    # ....
    # Configura Permissoes Autor
    op_autor.permissions.add(perms_autor)

    # Configura Permissoes Operador de Administracao
    # .....
    for p in perms_docadm:
        op_adm.permissions.add(p)

if __name__ == '__main__':
    cria_grupos_permissoes()
