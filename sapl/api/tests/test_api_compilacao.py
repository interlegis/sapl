import pytest
from django.contrib.contenttypes.models import ContentType
from model_bakery import baker

from sapl.api.tests.conftest import ids, resultados
from sapl.base.models import Autor
from sapl.compilacao.models import (STATUS_TA_EDITION,
                                    STATUS_TA_IMMUTABLE_PUBLIC,
                                    STATUS_TA_IMMUTABLE_RESTRICT,
                                    STATUS_TA_PRIVATE, STATUS_TA_PUBLIC,
                                    Dispositivo, Nota, Publicacao,
                                    TextoArticulado, Vide)
from sapl.materia.models import (Proposicao, TipoMateriaLegislativa,
                                 TipoProposicao)

URL_TA = '/api/compilacao/textoarticulado/'
URL_DISPOSITIVO = '/api/compilacao/dispositivo/'
URL_NOTA = '/api/compilacao/nota/'
URL_VIDE = '/api/compilacao/vide/'
URL_PUBLICACAO = '/api/compilacao/publicacao/'

PUBLICO, IMUTAVEL_PUBLICO = STATUS_TA_PUBLIC, STATUS_TA_IMMUTABLE_PUBLIC
RESTRITO, EDICAO, PRIVADO = (STATUS_TA_IMMUTABLE_RESTRICT, STATUS_TA_EDITION,
                             STATUS_TA_PRIVATE)
TODOS_OS_STATUS = (PUBLICO, IMUTAVEL_PUBLICO, RESTRITO, EDICAO, PRIVADO)

PERM_VER_RESTRITO = 'compilacao.view_restricted_textoarticulado'
PERM_EDICAO_DINAMICA = 'compilacao.change_dispositivo_edicao_dinamica'


def _dispositivo(ta, ordem, **kwargs):
    kwargs.setdefault('texto', f'texto do dispositivo {ordem} de {ta.pk}')
    return baker.make(Dispositivo, ta=ta, ordem=ordem, **kwargs)


@pytest.fixture
def dono(usuario):
    return usuario('dono')


@pytest.fixture
def textos(dono):
    """Um TA com um dispositivo para cada nível de privacidade."""
    tas = {}
    for status in TODOS_OS_STATUS:
        ta = baker.make(TextoArticulado, privacidade=status,
                        ementa=f'ementa {status}')
        ta.owners.add(dono)
        _dispositivo(ta, 1000)
        tas[status] = ta
    return tas


def _ids_ta(textos, *status):
    return {textos[s].pk for s in status}


def _ids_dispositivos(textos, *status):
    return set(Dispositivo.objects.filter(
        ta__in=[textos[s] for s in status]).values_list('pk', flat=True))


CENARIOS = [
    # (usuário, permissões, status visíveis)
    (None, (), (PUBLICO, IMUTAVEL_PUBLICO)),
    ('sem_permissao', (), (PUBLICO, IMUTAVEL_PUBLICO)),
    ('dono', (), TODOS_OS_STATUS),
    ('leitor_restrito', (PERM_VER_RESTRITO,),
     (PUBLICO, IMUTAVEL_PUBLICO, RESTRITO)),
    ('editor', (PERM_EDICAO_DINAMICA,), (PUBLICO, IMUTAVEL_PUBLICO, EDICAO)),
]


def _cliente(api, usuario, dono, username, perms):
    if username is None:
        return api()
    if username == 'dono':
        return api(dono)
    return api(usuario(username, *perms))


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('username, perms, visiveis', CENARIOS)
def test_lista_de_textos_articulados_respeita_privacidade(
        api, usuario, dono, textos, username, perms, visiveis):
    response = _cliente(api, usuario, dono, username, perms).get(URL_TA)

    assert response.status_code == 200
    assert ids(response) == _ids_ta(textos, *visiveis)


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('username, perms, visiveis', CENARIOS)
def test_detalhe_de_texto_articulado_respeita_privacidade(
        api, usuario, dono, textos, username, perms, visiveis):
    client = _cliente(api, usuario, dono, username, perms)

    for status, ta in textos.items():
        response = client.get(f'{URL_TA}{ta.pk}/')
        assert response.status_code == (200 if status in visiveis else 404), \
            status


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('username, perms, visiveis', CENARIOS)
def test_lista_de_dispositivos_respeita_privacidade_do_texto(
        api, usuario, dono, textos, username, perms, visiveis):
    client = _cliente(api, usuario, dono, username, perms)

    response = client.get(URL_DISPOSITIVO)
    assert response.status_code == 200
    assert ids(response) == _ids_dispositivos(textos, *visiveis)

    for status, ta in textos.items():
        response = client.get(URL_DISPOSITIVO, {'ta': ta.pk})
        esperado = _ids_dispositivos(textos, status) \
            if status in visiveis else set()
        assert ids(response) == esperado, status


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('username, perms, visiveis', CENARIOS)
def test_detalhe_de_dispositivo_respeita_privacidade_do_texto(
        api, usuario, dono, textos, username, perms, visiveis):
    client = _cliente(api, usuario, dono, username, perms)

    for status, ta in textos.items():
        dispositivo = ta.dispositivos_set.get()
        response = client.get(f'{URL_DISPOSITIVO}{dispositivo.pk}/')
        assert response.status_code == (200 if status in visiveis else 404), \
            status


@pytest.mark.django_db(transaction=False)
def test_superusuario_nao_ve_texto_privado_de_outro_dono(
        api, usuario, textos):
    admin = usuario('admin', is_superuser=True, is_staff=True)

    response = api(admin).get(URL_TA)

    assert ids(response) == _ids_ta(
        textos, PUBLICO, IMUTAVEL_PUBLICO, RESTRITO, EDICAO)


@pytest.mark.django_db(transaction=False)
def test_dispositivo_alterado_segue_visibilidade_no_texto_publicado(api):
    """
    Um dispositivo aparece no texto a que pertence (ta) e, se
    visibilidade=True, também no bloco de alteração do texto que o
    publicou (ta_publicado), como em compilacao/text_list_blocoalteracao.html.
    """
    publico = baker.make(TextoArticulado, privacidade=PUBLICO)
    privado = baker.make(TextoArticulado, privacidade=PRIVADO)

    visivel_no_publicado = _dispositivo(
        privado, 1000, ta_publicado=publico, visibilidade=True)
    oculto_no_publicado = _dispositivo(
        privado, 2000, ta_publicado=publico, visibilidade=False)
    do_texto_publico = _dispositivo(
        publico, 1000, ta_publicado=privado, visibilidade=False)

    response = api().get(URL_DISPOSITIVO)

    assert ids(response) == {visivel_no_publicado.pk, do_texto_publico.pk}
    assert oculto_no_publicado.pk not in ids(
        api().get(URL_DISPOSITIVO, {'ta_publicado': publico.pk}))


@pytest.fixture
def proposicao_em_rascunho(usuario):
    """
    Proposição com texto articulado criado como em ProposicaoTaView:
    privado e tendo como dono o operador do autor.
    """
    operador = usuario('operador_do_autor')
    autor = baker.make(Autor, nome='Vereador Autor')
    autor.operadores.add(operador)
    tipo = baker.make(
        TipoProposicao,
        content_type=ContentType.objects.get_for_model(TipoMateriaLegislativa),
        object_id=baker.make(TipoMateriaLegislativa).pk)
    proposicao = baker.make(Proposicao, autor=autor, tipo=tipo,
                            data_envio=None, data_recebimento=None)
    ta = TextoArticulado.objects.create(
        content_object=proposicao, ementa='Minuta sigilosa', numero='1',
        ano=2026, privacidade=STATUS_TA_PRIVATE,
        editable_only_by_owners=True, editing_locked=False)
    ta.owners.add(operador)
    _dispositivo(ta, 1000, texto='Art. 1º Texto ainda não enviado.')
    return proposicao, ta, operador


@pytest.mark.django_db(transaction=False)
def test_texto_de_proposicao_em_rascunho_nao_e_publico(
        api, usuario, proposicao_em_rascunho):
    _, ta, operador = proposicao_em_rascunho
    anonimo = api()

    assert anonimo.get(f'{URL_TA}{ta.pk}/').status_code == 404
    response = anonimo.get(URL_DISPOSITIVO, {'ta': ta.pk})
    assert response.status_code == 200
    assert resultados(response) == []

    # nem quem pode ver textos restritos vê um rascunho que não é seu
    protocolo = api(usuario('protocolo', PERM_VER_RESTRITO))
    assert protocolo.get(f'{URL_TA}{ta.pk}/').status_code == 404
    assert resultados(protocolo.get(URL_DISPOSITIVO, {'ta': ta.pk})) == []

    # o dono continua lendo o próprio rascunho pela API
    response = api(operador).get(URL_DISPOSITIVO, {'ta': ta.pk})
    assert [d['texto'] for d in resultados(response)] == [
        'Art. 1º Texto ainda não enviado.']


@pytest.mark.django_db(transaction=False)
def test_texto_de_proposicao_enviada_e_restrito(
        api, usuario, proposicao_em_rascunho):
    _, ta, _ = proposicao_em_rascunho
    # como em sapl.materia.views.ProposicaoView ao enviar
    ta.privacidade = STATUS_TA_IMMUTABLE_RESTRICT
    ta.editing_locked = True
    ta.save()

    assert api().get(f'{URL_TA}{ta.pk}/').status_code == 404
    assert resultados(api().get(URL_DISPOSITIVO, {'ta': ta.pk})) == []

    protocolo = api(usuario('protocolo', PERM_VER_RESTRITO))
    assert protocolo.get(f'{URL_TA}{ta.pk}/').status_code == 200
    assert len(resultados(protocolo.get(URL_DISPOSITIVO, {'ta': ta.pk}))) == 1


# Notas, vides e publicações: as mesmas regras da tela do texto (TextView)

NPRIV, NINST, NPUBL = Nota.NPRIV, Nota.NINST, Nota.NPUBL


def _todos(client, url, **params):
    """Ids de uma listagem pequena, sem depender da página padrão."""
    response = client.get(url, dict(params, page_size=100))
    assert response.status_code == 200
    return ids(response)


@pytest.fixture
def autor_das_notas(usuario):
    return usuario('autor_das_notas')


@pytest.fixture
def cliente(api, usuario, dono, autor_das_notas):
    """Cliente da API para cada perfil usado nos cenários abaixo."""
    def _cliente(nome):
        if nome is None:
            return api()
        if nome == 'dono':
            return api(dono)
        if nome == 'autor_das_notas':
            return api(autor_das_notas)
        if nome == 'admin':
            return api(usuario('admin', is_superuser=True, is_staff=True))
        perms = {'leitor_restrito': (PERM_VER_RESTRITO,),
                 'editor': (PERM_EDICAO_DINAMICA,)}.get(nome, ())
        return api(usuario(nome, *perms))
    return _cliente


@pytest.fixture
def notas(textos, autor_das_notas):
    """
    Uma nota de cada publicidade no dispositivo de cada texto, todas do
    mesmo autor.
    """
    criadas = {}
    for status, ta in textos.items():
        dispositivo = ta.dispositivos_set.get()
        for publicidade in (NPRIV, NINST, NPUBL):
            criadas[status, publicidade] = baker.make(
                Nota, dispositivo=dispositivo, owner=autor_das_notas,
                publicidade=publicidade,
                texto=f'nota {publicidade} do texto {status}')
    return criadas


CENARIOS_NOTAS = [
    # (usuário, textos visíveis, publicidades visíveis), como em
    # compilacao/text_list_bloco.html
    (None, (PUBLICO, IMUTAVEL_PUBLICO), (NPUBL,)),
    ('sem_permissao', (PUBLICO, IMUTAVEL_PUBLICO), (NPUBL, NINST)),
    ('autor_das_notas', (PUBLICO, IMUTAVEL_PUBLICO), (NPUBL, NINST, NPRIV)),
    ('dono', TODOS_OS_STATUS, (NPUBL, NINST)),
    ('leitor_restrito', (PUBLICO, IMUTAVEL_PUBLICO, RESTRITO),
     (NPUBL, NINST)),
    ('admin', (PUBLICO, IMUTAVEL_PUBLICO, RESTRITO, EDICAO),
     (NPUBL, NINST, NPRIV)),
]


def _ids_notas(notas, textos_visiveis, publicidades):
    return {nota.pk for (status, publicidade), nota in notas.items()
            if status in textos_visiveis and publicidade in publicidades}


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('nome, textos_visiveis, publicidades', CENARIOS_NOTAS)
def test_lista_de_notas_respeita_publicidade_e_texto(
        cliente, notas, nome, textos_visiveis, publicidades):
    assert _todos(cliente(nome), URL_NOTA) == _ids_notas(
        notas, textos_visiveis, publicidades)


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('nome, textos_visiveis, publicidades', CENARIOS_NOTAS)
def test_detalhe_de_nota_respeita_publicidade_e_texto(
        cliente, notas, nome, textos_visiveis, publicidades):
    client = cliente(nome)
    visiveis = _ids_notas(notas, textos_visiveis, publicidades)

    for (status, publicidade), nota in notas.items():
        response = client.get(f'{URL_NOTA}{nota.pk}/')
        assert response.status_code == (
            200 if nota.pk in visiveis else 404), (status, publicidade)


@pytest.mark.django_db(transaction=False)
def test_anonimo_nao_le_nota_privada_nem_texto_privado_pelas_notas(
        api, autor_das_notas):
    """
    Antes, /api/compilacao/nota/?expand=dispositivo mostrava a um anônimo
    as notas privadas e, por meio de uma nota pública, o texto de um
    dispositivo de um texto articulado privado.
    """
    publico = baker.make(TextoArticulado, privacidade=PUBLICO)
    privado = baker.make(TextoArticulado, privacidade=PRIVADO)
    publicado = _dispositivo(publico, 1000, texto='Art. 1º Texto publicado.')
    minuta = _dispositivo(privado, 1000, texto='Art. 1º Minuta sigilosa.')
    nota_publica = baker.make(
        Nota, dispositivo=publicado, owner=autor_das_notas,
        publicidade=NPUBL, texto='Nota pública')
    baker.make(Nota, dispositivo=publicado, owner=autor_das_notas,
               publicidade=NPRIV, texto='Anotação pessoal')
    baker.make(Nota, dispositivo=minuta, owner=autor_das_notas,
               publicidade=NPUBL, texto='Nota pública sobre a minuta')

    response = api().get(URL_NOTA, {'expand': 'dispositivo'})

    assert response.status_code == 200
    assert [(n['id'], n['dispositivo']['texto'])
            for n in resultados(response)] == [
        (nota_publica.pk, 'Art. 1º Texto publicado.')]
    conteudo = response.content.decode()
    assert 'Anotação pessoal' not in conteudo
    assert 'Minuta sigilosa' not in conteudo


CENARIOS_TA = [(nome, visiveis) for nome, _, visiveis in CENARIOS] + [
    ('admin', (PUBLICO, IMUTAVEL_PUBLICO, RESTRITO, EDICAO)),
]


@pytest.fixture
def vides(textos):
    """
    Vides entre dispositivos de textos com privacidades diferentes, nos dois
    sentidos, indexados por (privacidade do dispositivo_base, privacidade do
    dispositivo_ref).
    """
    dispositivos = {status: ta.dispositivos_set.get()
                    for status, ta in textos.items()}
    outro_privado = _dispositivo(textos[PRIVADO], 2000)
    pares = {
        (PUBLICO, PRIVADO): (dispositivos[PUBLICO], dispositivos[PRIVADO]),
        (PRIVADO, IMUTAVEL_PUBLICO): (dispositivos[PRIVADO],
                                      dispositivos[IMUTAVEL_PUBLICO]),
        (RESTRITO, PRIVADO): (dispositivos[RESTRITO], dispositivos[PRIVADO]),
        (PRIVADO, EDICAO): (dispositivos[PRIVADO], dispositivos[EDICAO]),
        (PRIVADO, PRIVADO): (dispositivos[PRIVADO], outro_privado),
    }
    return {par: baker.make(Vide, dispositivo_base=base, dispositivo_ref=ref,
                            texto=f'vide {par}')
            for par, (base, ref) in pares.items()}


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('nome, textos_visiveis', CENARIOS_TA)
def test_vide_e_visivel_se_um_dos_dispositivos_for(
        cliente, vides, nome, textos_visiveis):
    """
    Na tela, o vide aparece no texto do dispositivo_base (cita) e no do
    dispositivo_ref (citado).
    """
    client = cliente(nome)
    visiveis = {vide.pk for (base, ref), vide in vides.items()
                if base in textos_visiveis or ref in textos_visiveis}

    assert _todos(client, URL_VIDE) == visiveis
    for par, vide in vides.items():
        response = client.get(f'{URL_VIDE}{vide.pk}/')
        assert response.status_code == (
            200 if vide.pk in visiveis else 404), par


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('nome, textos_visiveis', CENARIOS_TA)
def test_publicacao_segue_a_privacidade_do_texto(
        cliente, textos, nome, textos_visiveis):
    publicacoes = {status: baker.make(Publicacao, ta=ta)
                   for status, ta in textos.items()}
    client = cliente(nome)

    assert _todos(client, URL_PUBLICACAO) == {
        publicacoes[status].pk for status in textos_visiveis}
    for status, publicacao in publicacoes.items():
        response = client.get(f'{URL_PUBLICACAO}{publicacao.pk}/')
        assert response.status_code == (
            200 if status in textos_visiveis else 404), status


@pytest.mark.django_db(transaction=False)
def test_nota_e_vide_seguem_o_dispositivo_no_texto_que_o_publicou(
        api, autor_das_notas):
    """
    Como em /api/compilacao/dispositivo/, um dispositivo de texto privado é
    visível no texto público que o publicou se tiver visibilidade=True.
    """
    publico = baker.make(TextoArticulado, privacidade=PUBLICO)
    privado = baker.make(TextoArticulado, privacidade=PRIVADO)
    alterado = _dispositivo(privado, 1000, ta_publicado=publico,
                            visibilidade=True)
    oculto = _dispositivo(privado, 2000, ta_publicado=publico,
                          visibilidade=False)
    outro_oculto = _dispositivo(privado, 3000)

    nota = baker.make(Nota, dispositivo=alterado, owner=autor_das_notas,
                      publicidade=NPUBL)
    baker.make(Nota, dispositivo=oculto, owner=autor_das_notas,
               publicidade=NPUBL)
    vide = baker.make(Vide, dispositivo_base=oculto, dispositivo_ref=alterado)
    baker.make(Vide, dispositivo_base=oculto, dispositivo_ref=outro_oculto)

    assert _todos(api(), URL_NOTA) == {nota.pk}
    assert _todos(api(), URL_VIDE) == {vide.pk}
