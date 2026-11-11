import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from model_bakery import baker

from sapl.api.tests.conftest import ids, resultados
from sapl.base.models import DOC_ADM_OSTENSIVO, AppConfig
from sapl.materia.models import (HistoricoProposicao, MateriaLegislativa,
                                 Proposicao, Tramitacao)
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import (DocumentoAdministrativo,
                                      TramitacaoAdministrativo)
from sapl.sessao.models import RegistroLeitura, RegistroVotacao, VotoParlamentar

IP = '10.20.30.40'


def _proposicao_incorporada(**kwargs):
    materia = baker.make(MateriaLegislativa)
    return baker.make(
        Proposicao, data_envio=timezone.now(),
        data_recebimento=timezone.now(), cancelado=False,
        content_type=ContentType.objects.get_for_model(MateriaLegislativa),
        object_id=materia.pk, **kwargs)


def _documento_ostensivo(**kwargs):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)
    return baker.make(DocumentoAdministrativo, restrito=False, **kwargs)


def _tramitacao_administrativa(**kwargs):
    documento = _documento_ostensivo()
    return baker.make(TramitacaoAdministrativo, documento=documento, **kwargs)


# (model, fábrica, endpoint público para anônimos?)
MODELS_COM_IP_E_USER = [
    (MateriaLegislativa, None, True),
    (Tramitacao, None, True),
    (NormaJuridica, None, True),
    (Proposicao, _proposicao_incorporada, True),
    (HistoricoProposicao, None, False),
    (RegistroVotacao, None, True),
    (VotoParlamentar, None, True),
    (RegistroLeitura, None, True),
    (DocumentoAdministrativo, _documento_ostensivo, True),
    (TramitacaoAdministrativo, _tramitacao_administrativa, True),
]


def _url(model):
    return f'/api/{model._meta.app_label}/{model._meta.model_name}/'


def _perms(model, *radicais):
    return [f'{model._meta.app_label}.{radical}_{model._meta.model_name}'
            for radical in radicais]


@pytest.fixture
def cria(usuario):
    def _cria(model, fabrica):
        dono = usuario('quem_registrou')
        fabrica = fabrica or (lambda **kw: baker.make(model, **kw))
        return fabrica(ip=IP, user=dono)
    return _cria


def _parametros():
    return pytest.mark.parametrize(
        'model, fabrica, publico', MODELS_COM_IP_E_USER,
        ids=[m._meta.model_name for m, _, _ in MODELS_COM_IP_E_USER])


@pytest.mark.django_db(transaction=False)
@_parametros()
def test_ip_e_user_ocultos_para_anonimo(api, cria, model, fabrica, publico):
    if not publico:
        pytest.skip('endpoint não é público')
    obj = cria(model, fabrica)

    for response in (api().get(_url(model)),
                     api().get(f'{_url(model)}{obj.pk}/')):
        assert response.status_code == 200
        data = response.json()
        objeto = data['results'][0] if 'results' in data else data
        assert objeto['id'] == obj.pk
        assert 'ip' not in objeto and 'user' not in objeto


@pytest.mark.django_db(transaction=False)
@_parametros()
def test_ip_e_user_ocultos_sem_permissao_de_alteracao(
        api, usuario, cria, model, fabrica, publico):
    obj = cria(model, fabrica)
    leitor = usuario('leitor', *_perms(model, 'list', 'detail'))

    response = api(leitor).get(f'{_url(model)}{obj.pk}/')

    assert response.status_code == 200
    assert 'ip' not in response.json()
    assert 'user' not in response.json()


@pytest.mark.django_db(transaction=False)
@_parametros()
def test_ip_e_user_visiveis_com_permissao_de_alteracao(
        api, usuario, cria, model, fabrica, publico):
    obj = cria(model, fabrica)
    operador = usuario('operador', *_perms(model, 'list', 'detail', 'change'))

    response = api(operador).get(f'{_url(model)}{obj.pk}/')

    assert response.status_code == 200
    assert response.json()['ip'] == IP
    assert response.json()['user'] == obj.user_id


@pytest.mark.django_db(transaction=False)
@_parametros()
def test_filtro_por_ip_e_user_ignorado_sem_permissao_de_alteracao(
        api, usuario, cria, model, fabrica, publico):
    obj = cria(model, fabrica)
    leitor = usuario('leitor', *_perms(model, 'list', 'detail'))

    for filtro in ({'ip': '1.1.1.1'}, {'ip__startswith': '99.'},
                   {'user': obj.user_id + 1000}, {'user__isnull': 'true'}):
        response = api(leitor).get(_url(model), filtro)
        assert response.status_code == 200
        assert obj.pk in ids(response), filtro

    operador = usuario('operador', *_perms(model, 'list', 'detail', 'change'))
    response = api(operador).get(_url(model), {'ip__startswith': '99.'})
    assert obj.pk not in ids(response)


@pytest.mark.django_db(transaction=False)
def test_ultima_tramitacao_segue_a_mesma_regra(api, usuario, cria):
    tramitacao = cria(Tramitacao, None)
    url = (f'/api/materia/materialegislativa/{tramitacao.materia_id}/'
           'ultima_tramitacao/')

    response = api().get(url)
    assert response.status_code == 200
    assert response.json()['id'] == tramitacao.pk
    assert 'ip' not in response.json()

    operador = usuario('operador', 'materia.change_tramitacao')
    assert api(operador).get(url).json()['ip'] == IP


@pytest.mark.django_db(transaction=False)
def test_ip_e_user_ocultos_quando_expandidos(api, cria):
    tramitacao = cria(Tramitacao, None)

    response = api().get('/api/materia/tramitacao/',
                         {'expand': 'materia'})

    objeto = resultados(response)[0]
    assert objeto['id'] == tramitacao.pk
    assert isinstance(objeto['materia'], dict)
    assert 'ip' not in objeto['materia'] and 'user' not in objeto['materia']
