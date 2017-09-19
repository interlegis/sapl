import yaml
from django.conf import settings
from django.contrib.auth.models import Group, User


def le_yaml_dados_zope(caminho_yaml):
    with open(caminho_yaml, 'r') as f:
        dados = yaml.load(f.read())
    return dados

PERFIL_LEGADO_PARA_NOVO = [
    ('Autor', 'Autor'),
    ('Operador', 'Operador Geral'),
    ('Operador Comissao', 'Operador de Comissões'),
    ('Operador Materia', 'Operador de Matéria'),
    ('Operador Modulo Administrativo', 'Operador Administrativo'),
    ('Operador Norma', 'Operador de Norma Jurídica'),
    ('Operador Parlamentar', 'Parlamentar'),
    ('Operador Protocolo', 'Operador de Protocolo Administrativo'),
    ('Operador Sessao Plenaria', 'Operador de Sessão Plenária'),
]

ADMINISTRADORES = ['Administrador', 'Manager']

# XXX Esses não tem perfil novo e estão sendo ignorados
# TODO que fazer????
#
# Operador Mesa Diretora
# Operador Ordem Dia
# Operador Tabela Auxiliar
# Owner


VOTANTE = Group.objects.get(name='Votante')


def migra_usuarios(caminho_yaml):
    dados = le_yaml_dados_zope(caminho_yaml)
    db = settings.DATABASES['legacy']['NAME']
    nome, url, usuarios_perfis = dados[db]
    for nome, perfis in usuarios_perfis:
        usuario, _ = User.objects.get_or_create(username=nome)
        for legado, novo in PERFIL_LEGADO_PARA_NOVO:
            if legado in perfis:
                grupo = Group.objects.get(name=novo)
                usuario.groups.add(grupo)
            # Manager
            if any(a in perfis for a in ADMINISTRADORES):
                usuario.is_staff = True
                usuario.save()
            # Votante
            if 'Parlamentar' in perfis:
                usuario.groups.add(VOTANTE)
