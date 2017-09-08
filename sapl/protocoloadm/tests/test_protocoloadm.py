import datetime

import pytest
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.materia.models import UnidadeTramitacao
from sapl.protocoloadm.forms import (AnularProcoloAdmForm,
                                     DocumentoAdministrativoForm,
                                     MateriaLegislativa, ProtocoloDocumentForm,
                                     ProtocoloMateriaForm)
from sapl.protocoloadm.models import (DocumentoAdministrativo, Protocolo,
                                      StatusTramitacaoAdministrativo,
                                      TipoDocumentoAdministrativo,
                                      TipoMateriaLegislativa,
                                      TramitacaoAdministrativo)


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_acessivel(admin_client):
    response = admin_client.get(reverse('sapl.protocoloadm:anular_protocolo'))
    assert response.status_code == 200


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_submit(admin_client):
    mommy.make(Protocolo, numero='76', ano='2016', anulado=False)

    # TODO: setar usuario e IP
    response = admin_client.post(reverse('sapl.protocoloadm:anular_protocolo'),
                                 {'numero': '76',
                                  'ano': '2016',
                                  'justificativa_anulacao': 'TESTE',
                                  'salvar': 'Anular'},
                                 follow=True)

    assert response.status_code == 200

    protocolo = Protocolo.objects.first()
    assert protocolo.numero == 76
    assert protocolo.ano == 2016

    if not protocolo.anulado:
        pytest.fail(_("Protocolo deveria estar anulado"))
    assert protocolo.justificativa_anulacao == 'TESTE'


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_inexistente():
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})

    # Não usa o assert form.is_valid() == False por causa do PEP8
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))
    assert form.errors['__all__'] == [_("Protocolo 1/2016 não existe")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_valido():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=False)
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if not form.is_valid():
        pytest.fail(_("Form deve ser válido"))


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_anulado():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=True)
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.errors['__all__'] == \
        [_("Protocolo 1/2016 já encontra-se anulado")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_campos_obrigatorios():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=False)

    # TODO: generalizar para diminuir o tamanho deste método

    # numero ausente
    form = AnularProcoloAdmForm({'numero': '',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['numero'] == [_('Este campo é obrigatório.')]

    # ano ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['ano'] == [_('Este campo é obrigatório.')]

    # justificativa_anulacao ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': ''})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['justificativa_anulacao'] == \
                      [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_create_tramitacao(admin_client):
    tipo_doc = mommy.make(
        TipoDocumentoAdministrativo,
        descricao='Teste Tipo_DocAdm')

    documento_adm = mommy.make(
        DocumentoAdministrativo,
        tipo=tipo_doc)

    unidade_tramitacao_local_1 = mommy.make(
        UnidadeTramitacao, pk=1)

    unidade_tramitacao_destino_1 = mommy.make(
        UnidadeTramitacao, pk=2)

    unidade_tramitacao_destino_2 = mommy.make(
        UnidadeTramitacao, pk=3)

    status = mommy.make(
        StatusTramitacaoAdministrativo)

    tramitacao = mommy.make(
        TramitacaoAdministrativo,
        unidade_tramitacao_local=unidade_tramitacao_local_1,
        unidade_tramitacao_destino=unidade_tramitacao_destino_1,
        status=status,
        documento=documento_adm,
        data_tramitacao=datetime.date(2016, 8, 21))

    response = admin_client.post(
        reverse(
            'sapl.protocoloadm:tramitacaoadministrativo_create',
            kwargs={'pk': documento_adm.pk}),
        {'unidade_tramitacao_local': unidade_tramitacao_destino_2.pk,
         'unidade_tramitacao_destino': unidade_tramitacao_local_1.pk,
         'documento': documento_adm.pk,
         'status': status.pk,
         'data_tramitacao': datetime.date(2016, 8, 21)},
        follow=True)

    msg = force_text(_('A origem da nova tramitação deve ser igual ao '
                       'destino  da última adicionada!'))

    # Verifica se a origem da nova tramitacao é igual ao destino da última
    assert msg in response.context_data[
        'form'].errors['__all__']

    response = admin_client.post(
        reverse(
            'sapl.protocoloadm:tramitacaoadministrativo_create',
            kwargs={'pk': documento_adm.pk}),
        {'unidade_tramitacao_local': unidade_tramitacao_destino_1.pk,
         'unidade_tramitacao_destino': unidade_tramitacao_destino_2.pk,
         'documento': documento_adm.pk,
         'status': status.pk,
         'data_tramitacao': datetime.date(2016, 8, 20)},
        follow=True)

    msg = _('A data da nova tramitação deve ser ' +
            'maior que a data da última tramitação!')

    # Verifica se a data da nova tramitação é maior do que a última
    assert msg in response.context_data[
        'form'].errors['__all__']

    response = admin_client.post(
        reverse(
            'sapl.protocoloadm:tramitacaoadministrativo_create',
            kwargs={'pk': documento_adm.pk}),
        {'unidade_tramitacao_local': unidade_tramitacao_destino_1.pk,
         'unidade_tramitacao_destino': unidade_tramitacao_destino_2.pk,
         'documento': documento_adm.pk,
         'status': status.pk,
         'data_tramitacao': datetime.date.today() + datetime.timedelta(
             days=1)},
        follow=True)

    msg = force_text(_('A data de tramitação deve ser ' +
                       'menor ou igual a data de hoje!'))

    # Verifica se a data da tramitação é menor do que a data de hoje
    assert msg in response.context_data[
        'form'].errors['__all__']

    response = admin_client.post(
        reverse(
            'sapl.protocoloadm:tramitacaoadministrativo_create',
            kwargs={'pk': documento_adm.pk}),
        {'unidade_tramitacao_local': unidade_tramitacao_destino_1.pk,
         'unidade_tramitacao_destino': unidade_tramitacao_destino_2.pk,
         'documento': documento_adm.pk,
         'status': status.pk,
         'data_tramitacao': datetime.date(2016, 8, 21),
         'data_encaminhamento': datetime.date(2016, 8, 20)},
        follow=True)

    msg = force_text(_('A data de encaminhamento deve ser ' +
                       'maior que a data de tramitação!'))

    # Verifica se a data da encaminhamento é menor do que a data de tramitacao
    assert msg in response.context_data[
        'form'].errors['__all__']

    response = admin_client.post(
        reverse(
            'sapl.protocoloadm:tramitacaoadministrativo_create',
            kwargs={'pk': documento_adm.pk}),
        {'unidade_tramitacao_local': unidade_tramitacao_destino_1.pk,
         'unidade_tramitacao_destino': unidade_tramitacao_destino_2.pk,
         'documento': documento_adm.pk,
         'status': status.pk,
         'data_tramitacao': datetime.date(2016, 8, 21),
         'data_fim_prazo': datetime.date(2016, 8, 20)},
        follow=True)

    msg = _('A data fim de prazo deve ser ' +
            'maior que a data de tramitação!')

    # Verifica se a data da do fim do prazo é menor do que a data de tramitacao
    assert msg in response.context_data[
        'form'].errors['__all__']

    response = admin_client.post(
        reverse(
            'sapl.protocoloadm:tramitacaoadministrativo_create',
            kwargs={'pk': documento_adm.pk}),
        {'unidade_tramitacao_local': unidade_tramitacao_destino_1.pk,
         'unidade_tramitacao_destino': unidade_tramitacao_destino_2.pk,
         'documento': documento_adm.pk,
         'status': status.pk,
         'data_tramitacao': datetime.date(2016, 8, 21)},
        follow=True)

    tramitacao = TramitacaoAdministrativo.objects.last()
    # Verifica se a tramitacao que obedece as regras de negócios é criada
    assert tramitacao.data_tramitacao == datetime.date(2016, 8, 21)


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_dados_invalidos():

    form = AnularProcoloAdmForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['justificativa_anulacao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_form_anula_protocolo_inexistente():
    form = AnularProcoloAdmForm(data={'numero': '1',
                                      'ano': '2017',
                                      'justificativa_anulacao': 'teste'
                                      })

    assert not form.is_valid()

    assert form.errors['__all__'] == [_(
        'Protocolo 1/2017 não existe')]


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_form_anula_protocolo_anulado():
    mommy.make(Protocolo, numero=1, ano=2017, anulado=True)

    form = AnularProcoloAdmForm(data={'numero': '1',
                                      'ano': '2017',
                                      'justificativa_anulacao': 'teste'
                                      })

    assert not form.is_valid()

    assert form.errors['__all__'] == [_(
        'Protocolo 1/2017 já encontra-se anulado')]


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_form_anula_protocolo_com_doc_vinculado():
    tipo_materia = mommy.make(TipoMateriaLegislativa)

    mommy.make(Protocolo,
               numero=1,
               ano=2017,
               tipo_materia=tipo_materia,
               anulado=False)

    mommy.make(MateriaLegislativa,
               ano=2017,
               numero_protocolo=1)

    form = AnularProcoloAdmForm(data={'numero': '1',
                                      'ano': '2017',
                                      'justificativa_anulacao': 'teste'
                                      })

    assert not form.is_valid()

    assert form.errors['__all__'] == \
        [_("Protocolo 1/2017 não pode ser removido pois existem "
           "documentos vinculados a ele.")]

    tipo_documento = mommy.make(TipoDocumentoAdministrativo)

    protocolo_documento = mommy.make(Protocolo,
                                     numero=2,
                                     ano=2017,
                                     tipo_documento=tipo_documento,
                                     anulado=False)

    mommy.make(DocumentoAdministrativo,
               protocolo=protocolo_documento)

    form = AnularProcoloAdmForm(data={'numero': '2',
                                      'ano': '2017',
                                      'justificativa_anulacao': 'teste'
                                      })

    assert not form.is_valid()

    assert form.errors['__all__'] == \
        [_("Protocolo 2/2017 não pode ser removido pois existem "
           "documentos vinculados a ele.")]


def test_documento_administrativo_invalido():
    form = DocumentoAdministrativoForm(data={})

    assert not form.is_valid()

    errors = form.errors
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['assunto'] == [_('Este campo é obrigatório.')]
    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['data'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 5


@pytest.mark.django_db(transaction=False)
def test_documento_administrativo_protocolo_inexistente():

    tipo = mommy.make(TipoDocumentoAdministrativo)

    form = DocumentoAdministrativoForm(data={'ano': '2017',
                                             'tipo': str(tipo.pk),
                                             'assunto': 'teste',
                                             'numero': '1',
                                             'data': '2017-10-10',
                                             'numero_protocolo': '11',
                                             'ano_protocolo': '2017'
                                             })

    assert not form.is_valid()

    assert form.errors['__all__'] == [_('Protocolo 11/2017 inexistente.')]


def test_protocolo_documento_form_invalido():

    form = ProtocoloDocumentForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['tipo_protocolo'] == [_('Este campo é obrigatório.')]
    assert errors['interessado'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_documento'] == [_('Este campo é obrigatório.')]
    assert errors['numero_paginas'] == [_('Este campo é obrigatório.')]
    assert errors['assunto'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 5


def test_protocolo_materia_invalido():

    form = ProtocoloMateriaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['assunto_ementa'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_autor'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_materia'] == [_('Este campo é obrigatório.')]
    assert errors['numero_paginas'] == [_('Este campo é obrigatório.')]
    assert errors['autor'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 5
