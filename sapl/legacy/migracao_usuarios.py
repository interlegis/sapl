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


def migra_usuarios():
    """
    Lê o arquivo media/USERS e importa os usuários nele listados,
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

    ARQUIVO_USUARIOS = MEDIA_ROOT.child('USERS')
    with open(ARQUIVO_USUARIOS, 'r') as f:
        usuarios = eval(f.read())
    usuarios = [
        (nome,
         # troca senha "inicial" por uma inutilizável
         senha if senha != 'inicial' else None,
         # filtra perfis ignorados
         {p for p in perfis if p not in IGNORADOS})
        for nome, senha, perfis in usuarios]

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
