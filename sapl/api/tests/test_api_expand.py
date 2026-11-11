import datetime

import pytest
from model_bakery import baker

from sapl.api.tests.conftest import ids, resultados
from sapl.base.models import DOC_ADM_OSTENSIVO, AppConfig
from sapl.parlamentares.models import Filiacao, Mandato, Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo, Protocolo
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
