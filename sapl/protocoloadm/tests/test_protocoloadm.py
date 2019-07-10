from datetime import date, timedelta

from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy
from urllib.parse import urlencode
import pytest

from sapl.base.models import AppConfig
from sapl.comissoes.models import Comissao, TipoComissao
from sapl.materia.models import UnidadeTramitacao
from sapl.protocoloadm.forms import (AnularProtocoloAdmForm,
                                     DocumentoAdministrativoForm,
                                     MateriaLegislativa, ProtocoloDocumentForm,
                                     ProtocoloMateriaForm, TramitacaoAdmForm,
                                     TramitacaoAdmEditForm,
                                     compara_tramitacoes_doc,
                                     TramitacaoEmLoteAdmForm)
from sapl.protocoloadm.models import (DocumentoAdministrativo, Protocolo,
                                      StatusTramitacaoAdministrativo,
                                      TipoDocumentoAdministrativo,
                                      TipoMateriaLegislativa, Anexado,
                                      TramitacaoAdministrativo)
from sapl.utils import lista_anexados


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
    form = AnularProtocoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})

    # Não usa o assert form.is_valid() == False por causa do PEP8
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))
    assert form.errors['__all__'] == [_("Protocolo 1/2016 não existe")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_valido():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=False)
    form = AnularProtocoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if not form.is_valid():
        pytest.fail(_("Form deve ser válido"))


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_anulado():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=True)
    form = AnularProtocoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.errors['__all__'] == \
        [_("Protocolo 1/2016 já encontra-se anulado")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_campos_obrigatorios():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=False)

    # TODO: generalizar para diminuir o tamanho deste método

    # numero ausente
    form = AnularProtocoloAdmForm({'numero': '',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['numero'] == [_('Este campo é obrigatório.')]

    # ano ausente
    form = AnularProtocoloAdmForm({'numero': '1',
                                 'ano': '',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['ano'] == [_('Este campo é obrigatório.')]

    # justificativa_anulacao ausente
    form = AnularProtocoloAdmForm({'numero': '1',
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
        data_tramitacao=date(2016, 8, 21))

    response = admin_client.post(
        reverse(
            'sapl.protocoloadm:tramitacaoadministrativo_create',
            kwargs={'pk': documento_adm.pk}),
        {'unidade_tramitacao_local': unidade_tramitacao_destino_2.pk,
         'unidade_tramitacao_destino': unidade_tramitacao_local_1.pk,
         'documento': documento_adm.pk,
         'status': status.pk,
         'urgente': False,
         'texto': 'teste',
         'data_tramitacao': date(2016, 8, 21)},
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
         'urgente': False,
         'texto': 'teste',
         'data_tramitacao': date(2016, 8, 20)},
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
         'urgente': False,
         'texto': 'teste',
         'data_tramitacao': timezone.now().date() + timedelta(
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
         'urgente': False,
         'texto': 'teste',
         'data_tramitacao': date(2016, 8, 21),
         'data_encaminhamento': date(2016, 8, 20)},
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
         'urgente': False,
         'texto': 'teste',
         'data_tramitacao': date(2016, 8, 21),
         'data_fim_prazo': date(2016, 8, 20)},
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
         'urgente': False,
         'texto': 'teste',
         'data_tramitacao': date(2016, 8, 21)},
        follow=True)

    tramitacao = TramitacaoAdministrativo.objects.last()
    # Verifica se a tramitacao que obedece as regras de negócios é criada
    assert tramitacao.data_tramitacao == date(2016, 8, 21)


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_dados_invalidos():

    form = AnularProtocoloAdmForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['justificativa_anulacao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_form_anula_protocolo_inexistente():
    form = AnularProtocoloAdmForm(data={'numero': '1',
                                      'ano': '2017',
                                      'justificativa_anulacao': 'teste'
                                        })

    assert not form.is_valid()

    assert form.errors['__all__'] == [_(
        'Protocolo 1/2017 não existe')]


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_form_anula_protocolo_anulado():
    mommy.make(Protocolo, numero=1, ano=2017, anulado=True)

    form = AnularProtocoloAdmForm(data={'numero': '1',
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

    form = AnularProtocoloAdmForm(data={'numero': '1',
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

    form = AnularProtocoloAdmForm(data={'numero': '2',
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
    assert errors['restrito'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_documento_administrativo_protocolo_inexistente():

    tipo = mommy.make(TipoDocumentoAdministrativo)
    protocolo = mommy.make(Protocolo,
                           ano=2017,
                           numero=10,
                           anulado=False,
                           tipo_documento=tipo)

    form = DocumentoAdministrativoForm(data={'ano': '2017',
                                             'tipo': str(tipo.pk),
                                             'assunto': 'teste',
                                             'numero': '1',
                                             'data': '2017-10-10',
                                             'numero_protocolo': '11',
                                             'ano_protocolo': '2017',
                                             'restrito': False
                                             })

    assert not form.is_valid()

    assert form.errors['__all__'] == [_('Protocolo 11/2017 inexistente.')]


@pytest.mark.django_db(transaction=False)
def test_protocolo_documento_form_invalido():

    config = mommy.make(AppConfig)

    form = ProtocoloDocumentForm(
        data={},
        initial={
            'user_data_hora_manual': '',
            'ip_data_hora_manual': '',
            'data': timezone.localdate(timezone.now()),
            'hora':  timezone.localtime(timezone.now())})

    assert not form.is_valid()

    errors = form.errors

    assert errors['data_hora_manual'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_protocolo'] == [_('Este campo é obrigatório.')]
    assert errors['interessado'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_documento'] == [_('Este campo é obrigatório.')]
    assert errors['numero_paginas'] == [_('Este campo é obrigatório.')]
    assert errors['assunto'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_protocolo_materia_invalido():

    config = mommy.make(AppConfig)

    form = ProtocoloMateriaForm(data={},
                                initial={
        'user_data_hora_manual': '',
        'ip_data_hora_manual': '',
        'data': timezone.localdate(timezone.now()),
        'hora':  timezone.localtime(timezone.now())})

    assert not form.is_valid()

    errors = form.errors

    assert errors['data_hora_manual'] == [_('Este campo é obrigatório.')]
    assert errors['assunto_ementa'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_autor'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_materia'] == [_('Este campo é obrigatório.')]
    assert errors['numero_paginas'] == [_('Este campo é obrigatório.')]
    assert errors['autor'] == [_('Este campo é obrigatório.')]
    assert errors['vincular_materia'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 7


@pytest.mark.django_db(transaction=False)
def test_lista_documentos_anexados():
    tipo_documento = mommy.make(
            TipoDocumentoAdministrativo,
            descricao="Tipo_Teste"
    )
    documento_principal = mommy.make(
            DocumentoAdministrativo,
            numero=20,
            ano=2018,
            data="2018-01-04",
            tipo=tipo_documento
    )
    documento_anexado = mommy.make(
            DocumentoAdministrativo,
            numero=21,
            ano=2019,
            data="2019-05-04",
            tipo=tipo_documento
    )
    documento_anexado_anexado = mommy.make(
            DocumentoAdministrativo,
            numero=22,
            ano=2020,
            data="2020-01-05",
            tipo=tipo_documento
    )

    mommy.make(
            Anexado,
            documento_principal=documento_principal,
            documento_anexado=documento_anexado,
            data_anexacao="2019-05-11"
    )
    mommy.make(
            Anexado,
            documento_principal=documento_anexado,
            documento_anexado=documento_anexado_anexado,
            data_anexacao="2020-11-05"
    )

    lista = lista_anexados(documento_principal, False)
    
    assert len(lista) == 2
    assert lista[0] == documento_anexado
    assert lista[1] == documento_anexado_anexado


@pytest.mark.django_db(transaction=False)
def make_unidade_tramitacao(descricao):
    # Cria uma comissão para ser a unidade de tramitação
    tipo_comissao = mommy.make(TipoComissao)
    comissao = mommy.make(Comissao,
                          tipo=tipo_comissao,
                          nome=descricao,
                          sigla='T',
                          data_criacao='2016-03-21')

    # Testa a comissão
    assert comissao.tipo == tipo_comissao
    assert comissao.nome == descricao

    # Cria a unidade
    unidade = mommy.make(UnidadeTramitacao, comissao=comissao)
    assert unidade.comissao == comissao

    return unidade

        
@pytest.mark.django_db(transaction=False)
def test_tramitacoes_documentos_anexados(admin_client):

    config = mommy.make(AppConfig, tramitacao_documento=True)

    tipo_documento = mommy.make(
            TipoDocumentoAdministrativo,
            descricao="Tipo_Teste"
    )
    documento_principal = mommy.make(
            DocumentoAdministrativo,
            numero=20,
            ano=2018,
            data="2018-01-04",
            tipo=tipo_documento
    )
    documento_anexado = mommy.make(
            DocumentoAdministrativo,
            numero=21,
            ano=2019,
            data="2019-05-04",
            tipo=tipo_documento
    )
    documento_anexado_anexado = mommy.make(
            DocumentoAdministrativo,
            numero=22,
            ano=2020,
            data="2020-01-05",
            tipo=tipo_documento
    )

    mommy.make(
            Anexado,
            documento_principal=documento_principal,
            documento_anexado=documento_anexado,
            data_anexacao="2019-05-11"
    )
    mommy.make(
            Anexado,
            documento_principal=documento_anexado,
            documento_anexado=documento_anexado_anexado,
            data_anexacao="2020-11-05"
    )


    unidade_tramitacao_local_1 = make_unidade_tramitacao(descricao="Teste 1")
    unidade_tramitacao_destino_1 = make_unidade_tramitacao(descricao="Teste 2")
    unidade_tramitacao_destino_2 = make_unidade_tramitacao(descricao="Teste 3")

    status = mommy.make(
        StatusTramitacaoAdministrativo,
        indicador='R')

    # Teste criação de Tramitacao
    form = TramitacaoAdmForm(data={})
    form.data = {'data_tramitacao':date(2019, 5, 6),
                'unidade_tramitacao_local':unidade_tramitacao_local_1.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_1.pk,
                'status':status.pk,
                'urgente': False,
                'texto': "Texto de teste"}
    form.instance.documento_id=documento_principal.pk

    assert form.is_valid()
    tramitacao_principal = form.save()
    tramitacao_anexada = documento_anexado.tramitacaoadministrativo_set.last()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    # Verifica se foram criadas as tramitações para os documentos anexados e anexados aos anexados
    assert documento_principal.tramitacaoadministrativo_set.last() == tramitacao_principal
    assert tramitacao_principal.documento.tramitacao == (tramitacao_principal.status.indicador != "F")
    assert compara_tramitacoes_doc(tramitacao_principal, tramitacao_anexada)
    assert DocumentoAdministrativo.objects.get(id=documento_anexado.pk).tramitacao \
            == (tramitacao_anexada.status.indicador != "F")
    assert compara_tramitacoes_doc(tramitacao_anexada_anexada, tramitacao_principal)
    assert DocumentoAdministrativo.objects.get(id=documento_anexado_anexado.pk).tramitacao \
            == (tramitacao_anexada_anexada.status.indicador != "F")


    # Teste Edição de Tramitacao
    form = TramitacaoAdmEditForm(data={})
    # Alterando unidade_tramitacao_destino
    form.data = {'data_tramitacao':tramitacao_principal.data_tramitacao,
                'unidade_tramitacao_local':tramitacao_principal.unidade_tramitacao_local.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_2.pk,
                'status':tramitacao_principal.status.pk,
                'urgente': tramitacao_principal.urgente,
                'texto': tramitacao_principal.texto}
    form.instance = tramitacao_principal

    assert form.is_valid()
    tramitacao_principal = form.save()
    tramitacao_anexada = documento_anexado.tramitacaoadministrativo_set.last()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    assert tramitacao_principal.unidade_tramitacao_destino == unidade_tramitacao_destino_2
    assert tramitacao_anexada.unidade_tramitacao_destino == unidade_tramitacao_destino_2
    assert tramitacao_anexada_anexada.unidade_tramitacao_destino == unidade_tramitacao_destino_2


    # Teste Remoção de Tramitacao
    url = reverse('sapl.protocoloadm:tramitacaoadministrativo_delete', 
                    kwargs={'pk': tramitacao_principal.pk})
    response = admin_client.post(url, {'confirmar':'confirmar'} ,follow=True)
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_principal.pk).count() == 0
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_anexada.pk).count() == 0
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_anexada_anexada.pk).count() == 0
    
    
    # Testes para quando as tramitações das anexadas divergem
    form = TramitacaoAdmForm(data={})
    form.data = {'data_tramitacao':date(2019, 5, 6),
                'unidade_tramitacao_local':unidade_tramitacao_local_1.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_1.pk,
                'status':status.pk,
                'urgente': False,
                'texto': "Texto de teste"}
    form.instance.documento_id=documento_principal.pk

    assert form.is_valid()
    tramitacao_principal = form.save()
    tramitacao_anexada = documento_anexado.tramitacaoadministrativo_set.last()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    form = TramitacaoAdmEditForm(data={})
    # Alterando unidade_tramitacao_destino
    form.data = {'data_tramitacao':tramitacao_anexada.data_tramitacao,
                'unidade_tramitacao_local':tramitacao_anexada.unidade_tramitacao_local.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_2.pk,
                'status':tramitacao_anexada.status.pk,
                'urgente': tramitacao_anexada.urgente,
                'texto': tramitacao_anexada.texto}
    form.instance = tramitacao_anexada

    assert form.is_valid()
    tramitacao_anexada = form.save()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    assert tramitacao_principal.unidade_tramitacao_destino == unidade_tramitacao_destino_1
    assert tramitacao_anexada.unidade_tramitacao_destino == unidade_tramitacao_destino_2
    assert tramitacao_anexada_anexada.unidade_tramitacao_destino == unidade_tramitacao_destino_2

    # Editando a tramitação principal, as tramitações anexadas não devem ser editadas
    form = TramitacaoAdmEditForm(data={})
    # Alterando o texto
    form.data = {'data_tramitacao':tramitacao_principal.data_tramitacao,
                'unidade_tramitacao_local':tramitacao_principal.unidade_tramitacao_local.pk,
                'unidade_tramitacao_destino':tramitacao_principal.unidade_tramitacao_destino.pk,
                'status':tramitacao_principal.status.pk,
                'urgente': tramitacao_principal.urgente,
                'texto': "Testando a alteração"}
    form.instance = tramitacao_principal

    assert form.is_valid()
    tramitacao_principal = form.save()
    tramitacao_anexada = documento_anexado.tramitacaoadministrativo_set.last()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    assert tramitacao_principal.texto == "Testando a alteração"
    assert not tramitacao_anexada.texto == "Testando a alteração"
    assert not tramitacao_anexada_anexada.texto == "Testando a alteração"

    # Removendo a tramitação pricipal, as tramitações anexadas não devem ser removidas, pois divergiram
    url = reverse('sapl.protocoloadm:tramitacaoadministrativo_delete', 
                    kwargs={'pk': tramitacao_principal.pk})
    response = admin_client.post(url, {'confirmar':'confirmar'} ,follow=True)
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_principal.pk).count() == 0
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_anexada.pk).count() == 1
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_anexada_anexada.pk).count() == 1

    # Removendo a tramitação anexada, a tramitação anexada à anexada deve ser removida
    url = reverse('sapl.protocoloadm:tramitacaoadministrativo_delete', 
                    kwargs={'pk': tramitacao_anexada.pk})
    response = admin_client.post(url, {'confirmar':'confirmar'} ,follow=True)
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_anexada.pk).count() == 0
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_anexada_anexada.pk).count() == 0


    # Agora testando para caso não seja desejado tramitar os documentos anexados
    # junto com os documentos principais
    config.tramitacao_documento = False
    config.save()

    # Teste criação de Tramitacao
    form = TramitacaoAdmForm(data={})
    form.data = {'data_tramitacao':date(2019, 5, 6),
                'unidade_tramitacao_local':unidade_tramitacao_local_1.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_1.pk,
                'status':status.pk,
                'urgente': False,
                'texto': "Texto de teste"}
    form.instance.documento_id=documento_principal.pk

    assert form.is_valid()
    tramitacao_principal = form.save()
    tramitacao_anexada = documento_anexado.tramitacaoadministrativo_set.last()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    # Verifica se não foram criadas as tramitações para os documentos anexados e anexados aos anexados
    assert documento_principal.tramitacaoadministrativo_set.last() == tramitacao_principal
    assert tramitacao_principal.documento.tramitacao == (tramitacao_principal.status.indicador != "F")
    assert not tramitacao_anexada
    assert not tramitacao_anexada_anexada


    # Cria uma tramitação igual na tramitação anexada para testar a edição
    form = TramitacaoAdmForm(data={})
    form.data = {'data_tramitacao':date(2019, 5, 6),
                'unidade_tramitacao_local':unidade_tramitacao_local_1.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_1.pk,
                'status':status.pk,
                'urgente': False,
                'texto': "Texto de teste"}
    form.instance.documento_id=documento_anexado.pk

    assert form.is_valid()
    tramitacao_anexada = form.save()
    tramitacao_principal = documento_principal.tramitacaoadministrativo_set.last() 
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    assert documento_principal.tramitacaoadministrativo_set.all().count() == 1
    assert documento_anexado.tramitacaoadministrativo_set.last() == tramitacao_anexada
    assert not tramitacao_anexada_anexada

    form = TramitacaoAdmEditForm(data={})
    # Alterando unidade_tramitacao_destino da matéria principal, 
    # as anexadas não devem ser alteradas
    form.data = {'data_tramitacao':tramitacao_principal.data_tramitacao,
                'unidade_tramitacao_local':tramitacao_principal.unidade_tramitacao_local.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_2.pk,
                'status':tramitacao_principal.status.pk,
                'urgente': tramitacao_principal.urgente,
                'texto': tramitacao_principal.texto}
    form.instance = tramitacao_principal

    assert form.is_valid()
    tramitacao_principal = form.save()
    tramitacao_anexada = documento_anexado.tramitacaoadministrativo_set.last()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    assert tramitacao_principal.unidade_tramitacao_destino == unidade_tramitacao_destino_2
    assert tramitacao_anexada.unidade_tramitacao_destino == unidade_tramitacao_destino_1
    assert not tramitacao_anexada_anexada


    form = TramitacaoAdmEditForm(data={})
    # Alterando a anexada da principal para testar a remoção de tramitação
    form.data = {'data_tramitacao':tramitacao_principal.data_tramitacao,
                'unidade_tramitacao_local':tramitacao_principal.unidade_tramitacao_local.pk,
                'unidade_tramitacao_destino':unidade_tramitacao_destino_2.pk,
                'status':tramitacao_principal.status.pk,
                'urgente': tramitacao_principal.urgente,
                'texto': tramitacao_principal.texto}
    form.instance = tramitacao_anexada

    assert form.is_valid()
    tramitacao_anexada = form.save() 
    tramitacao_principal = documento_principal.tramitacaoadministrativo_set.last()
    tramitacao_anexada_anexada = documento_anexado_anexado.tramitacaoadministrativo_set.last()

    assert tramitacao_principal.unidade_tramitacao_destino == unidade_tramitacao_destino_2
    assert tramitacao_anexada.unidade_tramitacao_destino == unidade_tramitacao_destino_2
    assert not tramitacao_anexada_anexada
    assert compara_tramitacoes_doc(tramitacao_anexada, tramitacao_principal)

    # Removendo a tramitação principal, a tramitação anexada não deve ser removida
    url = reverse('sapl.protocoloadm:tramitacaoadministrativo_delete', 
                    kwargs={'pk': tramitacao_principal.pk})
    response = admin_client.post(url, {'confirmar':'confirmar'} ,follow=True)
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_principal.pk).count() == 0
    assert TramitacaoAdministrativo.objects.filter(id=tramitacao_anexada.pk).count() == 1


@pytest.mark.django_db(transaction=False)
def test_tramitacao_lote_documentos_form(admin_client):
    tipo_documento = mommy.make(
            TipoDocumentoAdministrativo,
            descricao="Tipo_Teste"
    )
    documento = mommy.make(
            DocumentoAdministrativo,
            numero=20,
            ano=2018,
            data="2019-05-16",
            tipo=tipo_documento
    )

    unidade_tramitacao_local_1 = make_unidade_tramitacao(descricao="Teste 1")
    unidade_tramitacao_destino_1 = make_unidade_tramitacao(descricao="Teste 2")

    status = mommy.make(
        StatusTramitacaoAdministrativo,
        indicador='R')

    # Form sem campos obrigatórios
    documentos = []
    form = TramitacaoEmLoteAdmForm(initial={'documentos': documentos}, data={})

    errors = form.errors
    assert errors['data_tramitacao'] == ['Este campo é obrigatório.']
    assert errors['unidade_tramitacao_local'] == ['Este campo é obrigatório.']
    assert errors['status'] == ['Este campo é obrigatório.']
    assert errors['unidade_tramitacao_destino'] == ['Este campo é obrigatório.']
    assert errors['texto'] == ['Este campo é obrigatório.']
    assert not form.is_valid()

    # Tramitar apenas um documento sem anexados
    documentos = [documento.id]
    now = timezone.now().date()

    form = TramitacaoEmLoteAdmForm(initial={'documentos': documentos}, data={})
    form.data = {'data_tramitacao': now + timedelta(days=5),
                'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                'status': status.id,
                'urgente': False,
                'texto': 'aaaa'}

    assert form.errors['__all__'] == \
        ["A data de tramitação deve ser menor ou igual a data de hoje!"]
    assert not form.is_valid()

    form = TramitacaoEmLoteAdmForm(initial={'documentos': documentos}, data={})
    form.data = {'data_tramitacao': '2019-05-14',
                'data_encaminhamento' : '2019-05-09',
                'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                'status': status.id,
                'urgente': False,
                'texto': 'aaaa'}

    assert form.errors['__all__'] == \
        ["A data de encaminhamento deve ser maior que a data de tramitação!"]
    assert not form.is_valid()

    form = TramitacaoEmLoteAdmForm(initial={'documentos': documentos}, data={})
    form.data = {'data_tramitacao': '2019-05-14',
                'data_encaminhamento' : '2019-05-15',
                'data_fim_prazo': '2019-05-09',
                'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                'status': status.id,
                'urgente': False,
                'texto': 'aaaa'}

    assert form.errors['__all__'] == \
        ["A data fim de prazo deve ser maior que a data de tramitação!"]
    assert not form.is_valid()

    form = TramitacaoEmLoteAdmForm(initial={'documentos': documentos}, data={})
    form.data = {'data_tramitacao': '2019-05-14',
                'data_encaminhamento' : '2019-05-15',
                'data_fim_prazo': '2019-05-18',
                'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                'status': status.id,
                'urgente': False,
                'texto': 'aaaa'}

    assert form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_tramitacao_lote_documentos_views(admin_client):
    config = mommy.make(AppConfig, tramitacao_documento=True)

    tipo_documento = mommy.make(
            TipoDocumentoAdministrativo,
            descricao="Tipo_Teste"
    )
    documento_principal = mommy.make(
            DocumentoAdministrativo,
            numero=20,
            ano=2018,
            data="2018-01-04",
            tipo=tipo_documento
    )
    documento_anexado = mommy.make(
            DocumentoAdministrativo,
            numero=21,
            ano=2019,
            data="2019-05-04",
            tipo=tipo_documento
    )
    documento_anexado_anexado = mommy.make(
            DocumentoAdministrativo,
            numero=22,
            ano=2020,
            data="2020-01-05",
            tipo=tipo_documento
    )

    documento_sem_anexados = mommy.make(
            DocumentoAdministrativo,
            numero=23,
            ano=2020,
            data="2021-01-05",
            tipo=tipo_documento
    )

    mommy.make(
            Anexado,
            documento_principal=documento_principal,
            documento_anexado=documento_anexado,
            data_anexacao="2019-05-11"
    )
    mommy.make(
            Anexado,
            documento_principal=documento_anexado,
            documento_anexado=documento_anexado_anexado,
            data_anexacao="2020-11-05"
    )

    unidade_tramitacao_local_1 = make_unidade_tramitacao(descricao="Teste 1")
    unidade_tramitacao_destino_1 = make_unidade_tramitacao(descricao="Teste 2")
    unidade_tramitacao_destino_2 = make_unidade_tramitacao(descricao="Teste 3")
    unidade_tramitacao_destino_3 = make_unidade_tramitacao(descricao="Teste 4")

    status = mommy.make(
        StatusTramitacaoAdministrativo,
        indicador='R')

    url = reverse('sapl.protocoloadm:primeira_tramitacao_em_lote_docadm')
    url = url + '?' + urlencode({'tipo':tipo_documento.id, 'data_0':'', 'data_1':''})

    response = admin_client.post(url, {'salvar':'salvar'}, follow=True)
    assert response.status_code == 200

    msgs = [m.message for m in response.context['messages']]
    assert len(msgs) == 1
    assert msgs[0] == 'Escolha algum Documento para ser tramitado.'

    documentos = [documento_sem_anexados.id, documento_anexado_anexado.id]

    response = admin_client.post(url, {'documentos': documentos,'salvar':'salvar'}, follow=True)
    msgs = [m.message for m in response.context['messages']]

    assert 'Data Tramitação: Este campo é obrigatório.' in msgs
    assert 'Unidade Local: Este campo é obrigatório.' in msgs
    assert 'Status: Este campo é obrigatório.' in msgs
    assert 'Unidade Destino: Este campo é obrigatório.' in msgs
    assert 'Texto da Ação: Este campo é obrigatório.' in msgs

    # Primeira tramitação em lote

    response = admin_client.post(url, 
                                    {'documentos': documentos,
                                    'data_tramitacao': date(2019, 5, 15),
                                    'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                                    'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                                    'status': status.id,
                                    'urgente': False,
                                    'texto': 'aaaa',
                                    'salvar':'salvar'}, 
                                follow=True)
    
    assert response.status_code == 200

    assert TramitacaoAdministrativo.objects.all().count() == 2
    assert documento_sem_anexados.tramitacaoadministrativo_set.all().count() == 1
    assert documento_anexado_anexado.tramitacaoadministrativo_set.all().count() == 1

    # Segunda tramitação em lote

    url_lote = reverse('sapl.protocoloadm:tramitacao_em_lote_docadm')
    url_lote = url_lote + '?' + urlencode(
                                    {'tipo':tipo_documento.id, 
                                    'tramitacaoadministrativo__unidade_tramitacao_destino':unidade_tramitacao_destino_1.id,
                                    'tramitacaoadministrativo__status': status.id,
                                    'data_0':'', 
                                    'data_1':''})

    response = admin_client.post(url_lote, {'salvar':'salvar'}, follow=True)
    assert response.status_code == 200

    assert response.context_data['object_list'].count() == 2

    msgs = [m.message for m in response.context['messages']]
    assert len(msgs) == 1
    assert msgs[0] == 'Escolha algum Documento para ser tramitado.'

    response = admin_client.post(url_lote, {'documentos':documentos, 'salvar':'salvar'}, follow=True)
    assert response.status_code == 200

    msgs = [m.message for m in response.context['messages']]

    assert 'Data Tramitação: Este campo é obrigatório.' in msgs
    assert 'Unidade Local: Este campo é obrigatório.' in msgs
    assert 'Status: Este campo é obrigatório.' in msgs
    assert 'Unidade Destino: Este campo é obrigatório.' in msgs
    assert 'Texto da Ação: Este campo é obrigatório.' in msgs
    
    response = admin_client.post(url_lote,
                                {'documentos': documentos,
                                'data_tramitacao': date(2019, 5, 15),
                                'unidade_tramitacao_local': unidade_tramitacao_destino_1.id,
                                'unidade_tramitacao_destino': unidade_tramitacao_destino_2.id,
                                'status': status.id,
                                'urgente': False,
                                'texto': 'aaaa',
                                'salvar':'salvar'}, 
                                follow=True)
    assert response.status_code == 200

    msgs = [m.message for m in response.context['messages']]

    assert 'Tramitação completa.' in msgs

    assert TramitacaoAdministrativo.objects.all().count() == 4
    assert documento_sem_anexados.tramitacaoadministrativo_set.all().count() == 2
    assert documento_anexado_anexado.tramitacaoadministrativo_set.all().count() == 2

    # Tramitar documentos com anexados
    # O documento anexado ao anexado não deve tramitar junto porque já está com tramitação diferente
    documentos = [documento_principal.id]

    response = admin_client.post(url, 
                                    {'documentos': documentos,
                                    'data_tramitacao': date(2019, 5, 15),
                                    'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                                    'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                                    'status': status.id,
                                    'urgente': False,
                                    'texto': 'aaaa',
                                    'salvar':'salvar'}, 
                                follow=True)
    
    assert response.status_code == 200

    assert TramitacaoAdministrativo.objects.all().count() == 6
    assert documento_principal.tramitacaoadministrativo_set.all().count() == 1
    assert documento_anexado.tramitacaoadministrativo_set.all().count() == 1

    # Segunda tramitação com documentos anexados
    response = admin_client.post(url_lote,
                                {'documentos': documentos,
                                'data_tramitacao': date(2019, 5, 15),
                                'unidade_tramitacao_local': unidade_tramitacao_destino_1.id,
                                'unidade_tramitacao_destino': unidade_tramitacao_destino_2.id,
                                'status': status.id,
                                'urgente': False,
                                'texto': 'aaaa',
                                'salvar':'salvar'}, 
                                follow=True)
    assert response.status_code == 200

    msgs = [m.message for m in response.context['messages']]

    assert 'Tramitação completa.' in msgs

    assert TramitacaoAdministrativo.objects.all().count() == 8
    assert documento_principal.tramitacaoadministrativo_set.all().count() == 2
    assert documento_anexado.tramitacaoadministrativo_set.all().count() == 2

    # Terceira tramitação em lote
    # Agora, o documento anexado ao anexado deve tramitar junto com o documento principal, 
    # pois suas tramitações convergiram

    response = admin_client.post(url_lote,
                                {'documentos': documentos,
                                'data_tramitacao': date(2019, 5, 15),
                                'unidade_tramitacao_local': unidade_tramitacao_destino_2.id,
                                'unidade_tramitacao_destino': unidade_tramitacao_destino_3.id,
                                'status': status.id,
                                'urgente': False,
                                'texto': 'aaaa',
                                'salvar':'salvar'}, 
                                follow=True)
    assert response.status_code == 200

    msgs = [m.message for m in response.context['messages']]

    assert 'Tramitação completa.' in msgs

    assert TramitacaoAdministrativo.objects.all().count() == 11
    assert documento_principal.tramitacaoadministrativo_set.all().count() == 3
    assert documento_anexado.tramitacaoadministrativo_set.all().count() == 3
    assert documento_anexado_anexado.tramitacaoadministrativo_set.all().count() == 3


    # Agora testando para caso não seja desejado tramitar os documentos anexados
    # junto com os documentos principais
    config.tramitacao_documento = False
    config.save()

    TramitacaoAdministrativo.objects.all().delete()
    assert TramitacaoAdministrativo.objects.all().count() == 0

    # Primeira tramitação em lote
    # Tramitar documentos com anexados
    # O documento anexado não deve tramitar junto com o prinicpal
    documentos = [documento_principal.id]

    response = admin_client.post(url, 
                                {'documentos': documentos,
                                'data_tramitacao': date(2019, 5, 15),
                                'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                                'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                                'status': status.id,
                                'urgente': False,
                                'texto': 'aaaa',
                                'salvar':'salvar'}, 
                                follow=True)
    
    assert response.status_code == 200

    assert TramitacaoAdministrativo.objects.all().count() == 1
    assert documento_principal.tramitacaoadministrativo_set.all().count() == 1
    assert documento_anexado.tramitacaoadministrativo_set.all().count() == 0
    assert documento_anexado_anexado.tramitacaoadministrativo_set.all().count() == 0

    # Tramitar o doc anexado ao principal para testar a segunda tramitação em lote
    documentos = [documento_anexado.id]

    response = admin_client.post(url, 
                                {'documentos': documentos,
                                'data_tramitacao': date(2019, 5, 15),
                                'unidade_tramitacao_local': unidade_tramitacao_local_1.id,
                                'unidade_tramitacao_destino': unidade_tramitacao_destino_1.id,
                                'status': status.id,
                                'urgente': False,
                                'texto': 'aaaa',
                                'salvar':'salvar'}, 
                                follow=True)
    
    assert response.status_code == 200

    assert TramitacaoAdministrativo.objects.all().count() == 2
    assert documento_principal.tramitacaoadministrativo_set.all().count() == 1
    assert documento_anexado.tramitacaoadministrativo_set.all().count() == 1
    assert documento_anexado_anexado.tramitacaoadministrativo_set.all().count() == 0

    tramitacao_principal = documento_principal.tramitacaoadministrativo_set.last()
    tramitacao_anexada = documento_anexado.tramitacaoadministrativo_set.last()
    assert compara_tramitacoes_doc(tramitacao_anexada, tramitacao_principal)

    documentos = [documento_principal.id]
    # Segunda tramitação, o documento anexado não deve tramitar com o principal
    response = admin_client.post(url_lote,
                                {'documentos': documentos,
                                'data_tramitacao': date(2019, 5, 15),
                                'unidade_tramitacao_local': unidade_tramitacao_destino_1.id,
                                'unidade_tramitacao_destino': unidade_tramitacao_destino_2.id,
                                'status': status.id,
                                'urgente': False,
                                'texto': 'aaaa',
                                'salvar':'salvar'}, 
                                follow=True)
    assert response.status_code == 200

    msgs = [m.message for m in response.context['messages']]

    assert 'Tramitação completa.' in msgs

    assert TramitacaoAdministrativo.objects.all().count() == 3
    assert documento_principal.tramitacaoadministrativo_set.all().count() == 2
    assert documento_anexado.tramitacaoadministrativo_set.all().count() == 1
    assert documento_anexado_anexado.tramitacaoadministrativo_set.all().count() == 0