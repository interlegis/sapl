import os
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")
django.setup()

if True:
    from django.apps import apps
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType


class InicializaGruposAutorizacoes():

    def cria_ou_reseta_grupo(self, nome):
        grupo = Group.objects.get_or_create(name=nome)[0]
        for p in list(grupo.permissions.all()):
            grupo.permissions.remove(p)
        return grupo

    def cria_usuario(self, nome, grupo):
        nome_usuario = nome
        usuario = get_user_model().objects.get_or_create(
            username=nome_usuario)[0]
        usuario.set_password('interlegis')
        usuario.save()
        grupo.user_set.add(usuario)

    def cria_grupos_permissoes(self):

        nomes_apps = ['base', 'parlamentares', 'comissoes',
                      'materia', 'norma', 'sessao', 'painel']

        permissoes = {app: list(Permission.objects.filter(
            content_type__in=ContentType.objects.filter(app_label=app)))
            for app in nomes_apps}

        # permissoes específicas para protocolo e documento administrativo
        cts = ContentType.objects.filter(app_label='protocoloadm')

        # documento administrativo
        permissoes['documento_administrativo'] = list(
            Permission.objects.filter(content_type__in=cts))
        nome_grupo = 'Operador Administrativo'
        grupo = self.cria_ou_reseta_grupo(nome_grupo)
        for p in permissoes['documento_administrativo']:
            grupo.permissions.add(p)

        nome_usuario = 'operador_administrativo'
        self.cria_usuario(nome_usuario, grupo)

        # prolocolo administrativo
        cts = cts.exclude(model__icontains='tramitacao').exclude(
            model__icontains='documentoadministrativo')
        permissoes['protocoloadm'] = list(
            Permission.objects.filter(content_type__in=cts))
        nome_grupo = 'Operador de Protocolo Administrativo'
        grupo = self.cria_ou_reseta_grupo(nome_grupo)
        for p in permissoes['protocoloadm']:
            grupo.permissions.add(p)

        nome_usuario = 'operador_protocoloadm'
        self.cria_usuario(nome_usuario, grupo)

        # permissoes do base
        cts = ContentType.objects.filter(app_label='base')
        permissoes['base'] = list(
            Permission.objects.filter(content_type__in=cts))

        for nome_app in nomes_apps:

            if nome_app not in {'base', 'parlamentares'}:
                # Elimina casos especificos

                # Cria Grupo
                nome_grupo = 'Operador de %s' % apps.get_app_config(
                    nome_app).verbose_name
                grupo = self.cria_ou_reseta_grupo(nome_grupo)

                # Elimina o acesso a proposicoes pelo Operador de Matérias
                if nome_app == 'materia':
                    cts = ContentType.objects.filter(
                        app_label='materia').exclude(model='proposicao')
                    permissoes['materia'] = list(
                        Permission.objects.filter(content_type__in=cts))

                # Configura as permissoes
                for p in permissoes[nome_app]:
                    grupo.permissions.add(p)

                # Cria o Usuario
                nome_usuario = 'operador_%s' % nome_app
                usuario = get_user_model().objects.get_or_create(
                    username=nome_usuario)[0]
                usuario.set_password('interlegis')
                usuario.save()
                grupo.user_set.add(usuario)

        # Operador Geral
        grupo_geral = self.cria_ou_reseta_grupo('Operador Geral')
        for lista in permissoes.values():
            for p in lista:
                grupo_geral.permissions.add(p)

        nome_usuario = 'operador_geral'
        self.cria_usuario(nome_usuario, grupo_geral)

        # Autor
        perms_autor = []
        perms_autor.append(Permission.objects.get(name='Can add Proposição'))
        perms_autor.append(
            Permission.objects.get(name='Can change Proposição'))
        perms_autor.append(
            Permission.objects.get(name='Can delete Proposição'))

        # Configura Permissoes Autor
        grupo = self.cria_ou_reseta_grupo('Autor')
        for p in perms_autor:
            grupo.permissions.add(p)

        nome_usuario = 'operador_autor'
        self.cria_usuario(nome_usuario, grupo)

    def __call__(self):
        self.cria_grupos_permissoes()


cria_grupos_permissoes = InicializaGruposAutorizacoes()
if __name__ == '__main__':
    cria_grupos_permissoes.cria_grupos_permissoes()
