import datetime

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from model_bakery import baker

from drfautoapi.drfautoapi import ExpandVisibility
from sapl.api.tests.conftest import ids, resultados
from sapl.base.models import DOC_ADM_OSTENSIVO, AppConfig
from sapl.compilacao.models import (STATUS_TA_PRIVATE, STATUS_TA_PUBLIC,
                                    Dispositivo, Nota, TextoArticulado, Vide)
from sapl.parlamentares.models import Filiacao, Mandato, Parlamentar
from sapl.protocoloadm.models import (Anexado, DocumentoAdministrativo,
                                     Protocolo)
from sapl.sessao.models import (SessaoPlenaria, SessaoPlenariaPresenca,
                                VotoParlamentar)

# campos de ParlamentarSerializerPublic.Meta.exclude
DADOS_PESSOAIS = {
    'cpf', 'rg', 'fax', 'data_nascimento', 'endereco_residencia',
    'municipio_residencia', 'uf_residencia', 'cep_residencia',
    'situacao_militar', 'telefone_residencia', 'titulo_eleitor',
    'fax_residencia',
}

PERM_PARLAMENTAR = 'parlamentares.add_parlamentar'


@pytest.fixture
def parlamentar(db):
    return baker.make(
        Parlamentar,
        nome_parlamentar='Fulano', nome_completo='Fulano de Tal',
        cpf='12345678900', rg='1234567', titulo_eleitor='123456789012',
        data_nascimento=datetime.date(1970, 1, 1),
        endereco_residencia='Rua Sigilosa, 1', municipio_residencia='Cidade',
        uf_residencia='PR', cep_residencia='85500000',
        telefone_residencia='4632200000', fax='4632200001',
        fax_residencia='4632200002', _fill_optional=['situacao_militar'])


@pytest.fixture
def outro_parlamentar(db):
    return baker.make(Parlamentar, nome_parlamentar='Beltrano',
                      cpf='98765432100',
                      data_nascimento=datetime.date(1980, 5, 5))


@pytest.fixture
def relacionados(parlamentar):
    """Um objeto de cada endpoint público que referencia o parlamentar."""
    sessao = baker.make(SessaoPlenaria,
                        data_inicio=datetime.date(2026, 1, 5), iniciada=True)
    return {
        '/api/parlamentares/mandato/': baker.make(
            Mandato, parlamentar=parlamentar),
        '/api/parlamentares/filiacao/': baker.make(
            Filiacao, parlamentar=parlamentar),
        '/api/sessao/sessaoplenariapresenca/': baker.make(
            SessaoPlenariaPresenca, parlamentar=parlamentar,
            sessao_plenaria=sessao),
        '/api/sessao/votoparlamentar/': baker.make(
            VotoParlamentar, parlamentar=parlamentar),
    }


URLS_COM_PARLAMENTAR = [
    '/api/parlamentares/mandato/',
    '/api/parlamentares/filiacao/',
    '/api/sessao/sessaoplenariapresenca/',
    '/api/sessao/votoparlamentar/',
]


def _parlamentar_expandido(response):
    assert response.status_code == 200
    objetos = resultados(response)
    assert len(objetos) == 1
    expandido = objetos[0]['parlamentar']
    assert isinstance(expandido, dict), expandido
    assert expandido['nome_parlamentar'] == 'Fulano'
    return expandido


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('url', URLS_COM_PARLAMENTAR)
@pytest.mark.parametrize('perms', [None, ()], ids=['anonimo', 'sem_permissao'])
def test_expand_de_parlamentar_nao_expoe_dados_pessoais(
        api, usuario, relacionados, url, perms):
    client = api() if perms is None else api(usuario('consulta', *perms))

    expandido = _parlamentar_expandido(
        client.get(url, {'expand': 'parlamentar'}))

    assert not DADOS_PESSOAIS & set(expandido)


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('url', URLS_COM_PARLAMENTAR)
def test_expand_de_parlamentar_com_permissao_mostra_dados_pessoais(
        api, usuario, relacionados, url):
    client = api(usuario('operador', PERM_PARLAMENTAR))

    expandido = _parlamentar_expandido(
        client.get(url, {'expand': 'parlamentar'}))

    assert DADOS_PESSOAIS <= set(expandido)
    assert expandido['cpf'] == '12345678900'


@pytest.mark.django_db(transaction=False)
def test_endpoint_de_parlamentar_continua_sem_dados_pessoais(
        api, usuario, parlamentar):
    for client in (api(), api(usuario('consulta'))):
        response = client.get(f'/api/parlamentares/parlamentar/{parlamentar.pk}/')
        assert response.status_code == 200
        assert not DADOS_PESSOAIS & set(response.json())

    response = api(usuario('operador', PERM_PARLAMENTAR)).get(
        f'/api/parlamentares/parlamentar/{parlamentar.pk}/')
    assert response.json()['cpf'] == '12345678900'


FILTROS_DE_DADOS_PESSOAIS = [
    {'cpf': '12345678900'},
    {'cpf__startswith': '123'},
    {'cpf__regex': '^1'},
    {'data_nascimento__year': '1970'},
    {'endereco_residencia__icontains': 'sigilosa'},
    {'titulo_eleitor__isnull': 'false', 'rg__startswith': '1'},
]


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('filtro', FILTROS_DE_DADOS_PESSOAIS)
def test_filtro_por_dado_pessoal_de_parlamentar_e_ignorado_sem_permissao(
        api, parlamentar, outro_parlamentar, filtro):
    """Sem isso, o filtro revelaria o CPF por tentativa e erro."""
    response = api().get('/api/parlamentares/parlamentar/', filtro)

    assert response.status_code == 200
    assert ids(response) == {parlamentar.pk, outro_parlamentar.pk}


@pytest.mark.django_db(transaction=False)
def test_ordenacao_por_dado_pessoal_de_parlamentar_e_ignorada_sem_permissao(
        api, parlamentar, outro_parlamentar):
    url = '/api/parlamentares/parlamentar/'
    padrao = [p['id'] for p in resultados(api().get(url))]

    for o in ('cpf,id', '-cpf,id', 'data_nascimento', '-data_nascimento'):
        response = api().get(url, {'o': o})
        assert [p['id'] for p in resultados(response)] == padrao, o


@pytest.mark.django_db(transaction=False)
def test_filtro_por_dado_pessoal_de_parlamentar_com_permissao(
        api, usuario, parlamentar, outro_parlamentar):
    client = api(usuario('operador', PERM_PARLAMENTAR))

    response = client.get('/api/parlamentares/parlamentar/',
                          {'cpf__startswith': '123'})

    assert ids(response) == {parlamentar.pk}


@pytest.mark.django_db(transaction=False)
def test_expand_nao_alcanca_model_que_o_usuario_nao_pode_listar(
        api, usuario):
    """
    Com documentos ostensivos, a listagem de documentos administrativos é
    pública, mas a de protocolos não: expandir 'protocolo' não pode
    contornar isso.
    """
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)
    protocolo = baker.make(Protocolo, interessado='Cidadão Interessado',
                           ip_data_hora_manual='10.0.0.1')
    baker.make(DocumentoAdministrativo, protocolo=protocolo, restrito=False)
    url = '/api/protocoloadm/documentoadministrativo/'

    assert api().get('/api/protocoloadm/protocolo/').status_code == 401

    response = api().get(url, {'expand': 'protocolo'})
    assert response.status_code == 200
    assert resultados(response)[0]['protocolo'] == protocolo.pk

    operador = usuario('protocolo', 'protocoloadm.list_protocolo',
                       'protocoloadm.detail_protocolo')
    response = api(operador).get(url, {'expand': 'protocolo'})
    assert resultados(response)[0]['protocolo']['interessado'] == \
        'Cidadão Interessado'


@pytest.mark.django_db(transaction=False)
def test_proposicoes_do_parlamentar_usam_o_serializer_de_proposicao(
        api, parlamentar):
    from django.contrib.contenttypes.models import ContentType
    from django.utils import timezone

    from sapl.base.models import Autor
    from sapl.materia.models import Proposicao

    autor = baker.make(
        Autor, nome='Fulano',
        content_type=ContentType.objects.get_for_model(Parlamentar),
        object_id=parlamentar.pk)
    proposicao = baker.make(
        Proposicao, autor=autor, descricao='Indicação recebida',
        data_envio=timezone.now(), data_recebimento=timezone.now(),
        cancelado=False)

    response = api().get(
        f'/api/parlamentares/parlamentar/{parlamentar.pk}/proposicoes/')

    assert response.status_code == 200
    assert [(p['id'], p['descricao']) for p in resultados(response)] == [
        (proposicao.pk, 'Indicação recebida')]


# Visibilidade de cada objeto expandido

def _num_queries(client, url, params):
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url, params)
    assert response.status_code == 200
    return len(queries)


def _texto_publico_e_privado():
    return (baker.make(TextoArticulado, privacidade=STATUS_TA_PUBLIC,
                       ementa='Lei publicada'),
            baker.make(TextoArticulado, privacidade=STATUS_TA_PRIVATE,
                       ementa='Minuta sigilosa'))


def _dispositivo_alterado(publico, privado, ordem=1000):
    """
    Dispositivo de um texto privado publicado num texto público: aparece
    no bloco de alteração do texto público (visibilidade=True), mas o texto
    a que pertence continua privado.
    """
    return baker.make(Dispositivo, ta=privado, ta_publicado=publico,
                      visibilidade=True, ordem=ordem,
                      texto=f'Art. {ordem} alterado.')


@pytest.mark.django_db(transaction=False)
def test_expand_mantem_so_o_id_do_objeto_que_o_usuario_nao_pode_ver(
        api, usuario):
    publico, privado = _texto_publico_e_privado()
    dono = usuario('dono')
    privado.owners.add(dono)
    dispositivo = _dispositivo_alterado(publico, privado)
    url = '/api/compilacao/dispositivo/'
    params = {'expand': 'ta;ta_publicado'}

    for response in (api().get(url, params),
                     api().get(f'{url}{dispositivo.pk}/', params)):
        assert response.status_code == 200
        obj = resultados(response)
        obj = obj[0] if isinstance(obj, list) else obj
        assert obj['id'] == dispositivo.pk
        assert obj['ta'] == privado.pk
        assert obj['ta_publicado']['ementa'] == 'Lei publicada'
        assert 'Minuta sigilosa' not in response.content.decode()

    # quem pode ver o texto privado continua recebendo o objeto expandido
    obj = resultados(api(dono).get(url, params))[0]
    assert obj['ta']['ementa'] == 'Minuta sigilosa'


@pytest.mark.django_db(transaction=False)
def test_expand_aninhado_mantem_so_o_id_do_objeto_oculto(api, usuario):
    publico, privado = _texto_publico_e_privado()
    dispositivo = _dispositivo_alterado(publico, privado)
    baker.make(Nota, dispositivo=dispositivo, owner=usuario('autor'),
               publicidade=Nota.NPUBL)

    response = api().get('/api/compilacao/nota/',
                         {'expand': 'dispositivo.ta,ta_publicado'})

    assert response.status_code == 200
    expandido = resultados(response)[0]['dispositivo']
    assert expandido['texto'] == 'Art. 1000 alterado.'
    assert expandido['ta'] == privado.pk
    assert expandido['ta_publicado']['ementa'] == 'Lei publicada'
    assert 'Minuta sigilosa' not in response.content.decode()


@pytest.mark.django_db(transaction=False)
def test_expand_dos_dispositivos_de_um_vide(api):
    publico, privado = _texto_publico_e_privado()
    citado = baker.make(Dispositivo, ta=publico, ordem=1000,
                        texto='Art. 1º Texto publicado.')
    minuta = baker.make(Dispositivo, ta=privado, ordem=1000,
                        texto='Art. 1º Texto da minuta.')
    baker.make(Vide, dispositivo_base=minuta, dispositivo_ref=citado)

    response = api().get('/api/compilacao/vide/',
                         {'expand': 'dispositivo_base;dispositivo_ref'})

    assert response.status_code == 200
    vide = resultados(response)[0]
    assert vide['dispositivo_base'] == minuta.pk
    assert vide['dispositivo_ref']['texto'] == 'Art. 1º Texto publicado.'
    assert 'Texto da minuta' not in response.content.decode()


@pytest.fixture
def documentos_anexados(db):
    """
    Com documentos administrativos ostensivos, qualquer pessoa lista os
    documentos, menos os restritos, que só usuários autenticados veem. O
    documento principal, público, tem um anexado ostensivo e um restrito.
    """
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)
    principal = baker.make(DocumentoAdministrativo, restrito=False,
                           assunto='Processo principal')
    ostensivo = baker.make(DocumentoAdministrativo, restrito=False,
                           assunto='Ofício ostensivo')
    restrito = baker.make(DocumentoAdministrativo, restrito=True,
                          assunto='Ofício restrito')
    for anexado in (ostensivo, restrito):
        baker.make(Anexado, documento_principal=principal,
                   documento_anexado=anexado)
    return principal, ostensivo, restrito


@pytest.mark.django_db(transaction=False)
def test_expand_many_to_many_mantem_so_o_id_dos_objetos_ocultos(
        api, usuario, documentos_anexados):
    principal, ostensivo, restrito = documentos_anexados
    url = '/api/protocoloadm/documentoadministrativo/'
    params = {'expand': 'anexados'}

    assert ids(api().get(url)) == {principal.pk, ostensivo.pk}

    for response in (api().get(f'{url}{principal.pk}/', params),
                     api().get(url, params)):
        assert response.status_code == 200
        obj = resultados(response)
        if isinstance(obj, list):
            obj = next(o for o in obj if o['id'] == principal.pk)
        assert [a for a in obj['anexados'] if isinstance(a, int)] == [
            restrito.pk]
        assert [a['assunto'] for a in obj['anexados']
                if isinstance(a, dict)] == ['Ofício ostensivo']
        assert 'Ofício restrito' not in response.content.decode()

    response = api(usuario('consulta')).get(f'{url}{principal.pk}/', params)
    assert {a['assunto'] for a in response.json()['anexados']} == {
        'Ofício ostensivo', 'Ofício restrito'}


@pytest.mark.django_db(transaction=False)
def test_visibilidade_dos_objetos_expandidos_e_verificada_em_lote(api):
    """
    O custo do expand de objetos ocultos não cresce com o tamanho da
    página: a visibilidade é verificada de uma vez para toda a listagem, e
    um objeto oculto não é buscado.
    """
    publico, privado = _texto_publico_e_privado()
    url = '/api/compilacao/dispositivo/'

    def custo_do_expand(n):
        while privado.dispositivos_set.count() < n:
            _dispositivo_alterado(
                publico, privado,
                ordem=1000 * (privado.dispositivos_set.count() + 1))
        params = {'ta_publicado': publico.pk}
        return (_num_queries(api(), url, dict(params, expand='ta')) -
                _num_queries(api(), url, params))

    assert custo_do_expand(2) == custo_do_expand(6)


@pytest.mark.django_db(transaction=False)
def test_visibilidade_do_expand_aninhado_e_verificada_em_lote(api, usuario):
    publico, privado = _texto_publico_e_privado()
    autor = usuario('autor')
    url = '/api/compilacao/nota/'

    def custo_do_expand_aninhado(n):
        while Nota.objects.count() < n:
            dispositivo = _dispositivo_alterado(
                publico, privado, ordem=1000 * (Nota.objects.count() + 1))
            baker.make(Nota, dispositivo=dispositivo, owner=autor,
                       publicidade=Nota.NPUBL)
        return (_num_queries(api(), url, {'expand': 'dispositivo.ta'}) -
                _num_queries(api(), url, {'expand': 'dispositivo'}))

    assert custo_do_expand_aninhado(2) == custo_do_expand_aninhado(6)


@pytest.mark.django_db(transaction=False)
def test_expand_verifica_objeto_a_objeto_se_nao_houver_como_fazer_em_lote(
        api, monkeypatch):
    """
    Se o caminho não puder ser verificado de uma vez (por exemplo, se passar
    por um campo que não é do model), cada objeto é verificado uma vez, e o
    oculto continua só com o id.
    """
    monkeypatch.setattr(ExpandVisibility, 'visible_in_path',
                        lambda self, root, path, model: None)
    publico, privado = _texto_publico_e_privado()
    dispositivos = [_dispositivo_alterado(publico, privado, ordem)
                    for ordem in (1000, 2000)]

    response = api().get('/api/compilacao/dispositivo/',
                         {'expand': 'ta;ta_publicado', 'o': 'ordem'})

    assert response.status_code == 200
    objetos = resultados(response)
    assert [o['id'] for o in objetos] == [d.pk for d in dispositivos]
    assert [o['ta'] for o in objetos] == [privado.pk, privado.pk]
    assert [o['ta_publicado']['id'] for o in objetos] == [
        publico.pk, publico.pk]
