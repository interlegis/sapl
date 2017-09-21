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

VOTANTE = Group.objects.get(name='Votante')


def migra_usuarios(caminho_yaml):
    """
    Existe um método em nosso projeto interno de **consulta a todos os sapls**
    que exporta os dados de usuários (e nome da casa e url interna)
    como um yaml.

    Esse yaml é lido por essa rotina e os usuários são criados se necessário
    e seus perfis ajustados.

    Os seguintes perfis no legado não correspondem a nenhum no código atual
    e estão sendo **ignorados**:

    * Operador Mesa Diretora
      Contei apenas **8 usuários**, em todas as bases, que tem esse perfil
      e não tem nem "Operador" nem "Operador Sessao Plenaria"

    * Operador Ordem Dia
      Contei apenas **16 usuários**, em todas as bases, que tem esse perfil
      e não tem nem "Operador" nem "Operador Sessao Plenaria"

    * Operador Tabela Auxiliar
      A edição das tabelas auxiliares deve ser feita por um administrador

    * Operador Lexml
      Também podemos assumir que essa é uma tarefa de um administrador
    """
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
