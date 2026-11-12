import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from drfautoapi import drfautoapi
from sapl.api.tests.conftest import ids, resultados, status_ou_erro
from sapl.base.models import DOC_ADM_OSTENSIVO, DOC_ADM_RESTRITIVO, AppConfig
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import Correspondencia, SessaoPlenaria

URL_CORRESPONDENCIA = '/api/sessao/correspondencia/'


def _correspondencia(sessao, numero_ordem, restrito):
    documento = baker.make(DocumentoAdministrativo, restrito=restrito,
                           assunto=f'Assunto do ofício {numero_ordem}')
    return baker.make(Correspondencia, sessao_plenaria=sessao,
                      documento=documento, numero_ordem=numero_ordem,
                      observacao=f'Observação da correspondência '
                                 f'{numero_ordem}')


@pytest.fixture
def correspondencias(db):
    """
    Uma sessão já realizada, com a correspondência de um documento ostensivo
    e a de um documento restrito, e uma sessão futura ainda não iniciada,
    oculta do público, com a correspondência de outro documento ostensivo.
    """
    realizada = baker.make(SessaoPlenaria,
                           data_inicio=datetime.date(2026, 1, 5),
                           iniciada=True)
    futura = baker.make(
        SessaoPlenaria,
        data_inicio=timezone.localdate() + datetime.timedelta(days=30),
        iniciada=False, publicar_pauta=False)
    return {
        'ostensiva': _correspondencia(realizada, 1, restrito=False),
        'restrita': _correspondencia(realizada, 2, restrito=True),
        'sessao_oculta': _correspondencia(futura, 1, restrito=False),
    }


def _detalhe(client, correspondencia):
    return client.get(f'{URL_CORRESPONDENCIA}{correspondencia.pk}/')


@pytest.mark.django_db(transaction=False)
def test_anonimo_no_modo_ostensivo_nao_ve_correspondencia_de_documento_restrito(
        api, correspondencias):
    """Como em CorrespondenciaCrud: o documento restrito oculta a linha."""
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)

    response = api().get(URL_CORRESPONDENCIA)

    assert response.status_code == 200
    assert ids(response) == {correspondencias['ostensiva'].pk}
    assert 'correspondência 2' not in response.content.decode()

    assert _detalhe(api(), correspondencias['ostensiva']).status_code == 200
    for chave in ('restrita', 'sessao_oculta'):
        assert _detalhe(api(), correspondencias[chave]).status_code == 404, \
            chave


@pytest.mark.django_db(transaction=False)
def test_anonimo_no_modo_restritivo_nao_ve_correspondencias(
        api, correspondencias):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_RESTRITIVO)

    response = api().get(URL_CORRESPONDENCIA)

    assert response.status_code == 200
    assert ids(response) == set()

    for chave, correspondencia in correspondencias.items():
        assert _detalhe(api(), correspondencia).status_code == 404, chave


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('modo', [DOC_ADM_OSTENSIVO, DOC_ADM_RESTRITIVO])
def test_usuario_autenticado_ve_todas_as_correspondencias(
        api, usuario, correspondencias, modo):
    """Na tela, basta estar conectado, sem permissão específica."""
    baker.make(AppConfig, documentos_administrativos=modo)
    client = api(usuario('servidor'))

    response = client.get(URL_CORRESPONDENCIA)

    assert response.status_code == 200
    assert ids(response) == {c.pk for c in correspondencias.values()}

    for chave, correspondencia in correspondencias.items():
        assert _detalhe(client, correspondencia).status_code == 200, chave


# Documentos das correspondências no ManyToMany SessaoPlenaria.correspondencias

URL_SESSAO = '/api/sessao/sessaoplenaria/'
PERMS_DOCUMENTO = ('protocoloadm.list_documentoadministrativo',
                   'protocoloadm.detail_documentoadministrativo')


def _correspondencias_da_sessao(client, correspondencias, **params):
    sessao = correspondencias['ostensiva'].sessao_plenaria
    response = client.get(f'{URL_SESSAO}{sessao.pk}/', params)
    assert response.status_code == 200
    return response.json()['correspondencias']


def _documentos(correspondencias, *chaves):
    return sorted(correspondencias[c].documento_id for c in chaves)


@pytest.mark.django_db(transaction=False)
def test_sessao_lista_ao_anonimo_so_os_documentos_que_ele_pode_ver(
        api, correspondencias):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)
    visiveis = _documentos(correspondencias, 'ostensiva')

    assert _correspondencias_da_sessao(api(), correspondencias) == visiveis

    pk = correspondencias['ostensiva'].sessao_plenaria_id
    response = api().get(URL_SESSAO)
    sessao = next(s for s in resultados(response) if s['id'] == pk)
    assert sessao['correspondencias'] == visiveis

    # com o expand, o documento oculto também é omitido, em vez de ficar só
    # com o id
    expandidos = _correspondencias_da_sessao(
        api(), correspondencias, expand='correspondencias')
    assert [d['id'] for d in expandidos] == visiveis


@pytest.mark.django_db(transaction=False)
def test_sessao_no_modo_restritivo_nao_lista_documentos_ao_anonimo(
        api, correspondencias):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_RESTRITIVO)

    assert _correspondencias_da_sessao(api(), correspondencias) == []
    assert _correspondencias_da_sessao(
        api(), correspondencias, expand='correspondencias') == []


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('modo, perms', [
    (DOC_ADM_OSTENSIVO, ()),
    (DOC_ADM_RESTRITIVO, PERMS_DOCUMENTO),
], ids=['ostensivo', 'restritivo'])
def test_sessao_lista_todos_os_documentos_a_quem_pode_ve_los(
        api, usuario, correspondencias, modo, perms):
    baker.make(AppConfig, documentos_administrativos=modo)
    client = api(usuario('servidor', *perms))
    todos = _documentos(correspondencias, 'ostensiva', 'restrita')

    assert sorted(_correspondencias_da_sessao(
        client, correspondencias)) == todos
    expandidos = _correspondencias_da_sessao(
        client, correspondencias, expand='correspondencias')
    assert sorted(d['id'] for d in expandidos) == todos


@pytest.mark.django_db(transaction=False)
def test_ids_das_correspondencias_seguem_a_visibilidade_dos_documentos(
        api, usuario, correspondencias):
    """
    O ManyToMany lista documentos, então segue a regra do endpoint de
    documentos: no modo restritivo, quem não pode listá-los não vê os ids,
    mesmo conectado. As correspondências continuam em
    /api/sessao/correspondencia/, como na tela.
    """
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_RESTRITIVO)
    client = api(usuario('servidor'))

    assert _correspondencias_da_sessao(client, correspondencias) == []
    assert len(ids(client.get(URL_CORRESPONDENCIA))) == 3


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('filtro', ['correspondencias',
                                    'correspondencias__in'])
def test_filtro_pelos_documentos_da_sessao_trata_o_oculto_como_inexistente(
        api, usuario, correspondencias, filtro):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)
    sessao = correspondencias['ostensiva'].sessao_plenaria_id
    ostensivo = correspondencias['ostensiva'].documento_id
    restrito = correspondencias['restrita'].documento_id
    inexistente = DocumentoAdministrativo.objects.order_by('-pk')[0].pk + 1

    assert ids(api().get(URL_SESSAO, {filtro: ostensivo})) == {sessao}

    oculto = status_ou_erro(api(), URL_SESSAO, {filtro: restrito})
    assert oculto != 200
    assert oculto == status_ou_erro(api(), URL_SESSAO, {filtro: inexistente})

    servidor = api(usuario('servidor'))
    assert ids(servidor.get(URL_SESSAO, {filtro: restrito})) == {sessao}


@pytest.mark.django_db(transaction=False)
def test_filtro_por_many_to_many_nao_usado_nao_avalia_os_documentos(
        api, monkeypatch):
    """
    A visibilidade dos documentos só é avaliada se o filtro for usado ou se
    a sessão tiver correspondências: avaliá-la custa as permissões da
    viewset de documentos e o AppConfig.
    """
    avaliados = []

    def visible_queryset(model, request):
        avaliados.append(model)
        return model.objects.none()

    monkeypatch.setattr(drfautoapi, 'visible_queryset', visible_queryset)
    baker.make(SessaoPlenaria, data_inicio=datetime.date(2026, 1, 5),
               iniciada=True)

    assert api().get(URL_SESSAO).status_code == 200
    assert avaliados == []

    status_ou_erro(api(), URL_SESSAO, {'correspondencias': 1})
    assert set(avaliados) == {DocumentoAdministrativo}
