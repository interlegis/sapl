import yaml
from django.contrib.auth.models import Group, User

from sapl.settings import MEDIA_ROOT

PERFIL_LEGADO_PARA_NOVO = {legado: Group.objects.get(name=novo)
                           for legado, novo in [
    ('Autor', 'Autor'),
    ('Operador', 'Operador Geral'),
    ('Operador Comissao', 'Operador de Comissões'),
    ('Operador Materia', 'Operador de Matéria'),
    ('Operador Modulo Administrativo', 'Operador Administrativo'),
    ('Operador Norma', 'Operador de Norma Jurídica'),
    ('Operador Parlamentar', 'Parlamentar'),
    ('Operador Protocolo', 'Operador de Protocolo Administrativo'),
    ('Operador Sessao Plenaria', 'Operador de Sessão Plenária'),
    ('Parlamentar', 'Votante'),
]
}

ADMINISTRADORES = {'Administrador', 'Manager'}

IGNORADOS = {
    # sem significado fora do zope
    'Alterar Senha', 'Authenticated', 'Owner',

    # obsoletos (vide docs a seguir)
    'Operador Mesa Diretora',
    'Operador Ordem Dia',
    'Operador Tabela Auxiliar',
    'Operador Lexml',
}


def decode_nome(nome):
    if isinstance(nome, bytes):
        try:
            return nome.decode('utf-8')
        except UnicodeDecodeError:
            return nome.decode('iso8859-1')
    else:
        assert isinstance(nome, str)
        return nome


def migra_usuarios():
    """
    Lê o arquivo media/usuarios.yaml e importa os usuários nele listados,
    com senhas e perfis.
    Os usuários são criados se necessário e seus perfis ajustados.

    Os seguintes perfis no legado não correspondem a nenhum no código atual
    e estão sendo **ignorados**:

    * Operador Mesa Diretora
      Apenas **8 usuários**, em todas as bases, têm esse perfil
      e não têm nem "Operador" nem "Operador Sessao Plenaria"

    * Operador Ordem Dia
      Apenas **16 usuários**, em todas as bases, têm esse perfil
      e não têm nem "Operador" nem "Operador Sessao Plenaria"

    * Operador Tabela Auxiliar
      A edição das tabelas auxiliares deve ser feita por um administrador

    * Operador Lexml
      Também podemos assumir que essa é uma tarefa de um administrador
    """

    ARQUIVO_USUARIOS = MEDIA_ROOT.child('usuarios.yaml')
    with open(ARQUIVO_USUARIOS, 'r') as f:
        usuarios = yaml.load(f)
    # conferimos de que só há um nome de usuário
    assert all(nome == dados['name'] for nome, dados in usuarios.items())
    usuarios = [
        (decode_nome(nome),
         # troca senha "inicial" (que existe em alguns zopes)
         # por uma inutilizável
         dados['__'] if dados['__'] != 'inicial' else None,
         # filtra perfis ignorados
         set(dados['roles']) - IGNORADOS)
        for nome, dados in usuarios.items()]

    for nome, senha, perfis in usuarios:
        usuario = User.objects.get_or_create(username=nome)[0]
        for perfil in perfis:
            if perfil in ADMINISTRADORES:
                # Manager
                usuario.is_staff = True
                usuario.save()
            else:
                usuario.groups.add(PERFIL_LEGADO_PARA_NOVO[perfil])
    # apaga arquivo (importante pois contém senhas)
    ARQUIVO_USUARIOS.remove()
