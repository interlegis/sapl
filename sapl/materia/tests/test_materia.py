from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from model_mommy import mommy
import pytest

from sapl.base.models import Autor, TipoAutor
from sapl.comissoes.models import Comissao, TipoComissao
from sapl.materia.models import (Anexada, Autoria, DespachoInicial,
                                 DocumentoAcessorio, MateriaLegislativa,
                                 Numeracao, Proposicao, RegimeTramitacao,
                                 StatusTramitacao, TipoDocumento,
                                 TipoMateriaLegislativa, TipoProposicao,
                                 Tramitacao, UnidadeTramitacao)
from sapl.norma.models import (LegislacaoCitada, NormaJuridica,
                               TipoNormaJuridica)
from sapl.utils import models_with_gr_for_model


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
def make_norma():
    # Cria um novo tipo de Norma
    tipo = mommy.make(TipoNormaJuridica,
                      sigla='T1',
                      descricao='Teste_Tipo_Norma')
    mommy.make(NormaJuridica,
               tipo=tipo,
               numero=1,
               ano=2016,
               data='2016-03-21',
               esfera_federacao='E',
               ementa='Teste_Ementa')

    # Testa se a Norma foi criada
    norma = NormaJuridica.objects.first()
    assert norma.tipo == tipo
    assert norma.numero == '1'
    assert norma.ano == 2016

    return norma


@pytest.mark.django_db(transaction=False)
def make_materia_principal():
    regime_tramitacao = mommy.make(RegimeTramitacao, descricao='Teste_Regime')

    # Cria a matéria principal
    tipo = mommy.make(TipoMateriaLegislativa,
                      sigla='T1',
                      descricao='Teste_MateriaLegislativa')
    mommy.make(MateriaLegislativa,
               tipo=tipo,
               numero='165',
               ano='2002',
               data_apresentacao='2003-01-01',
               regime_tramitacao=regime_tramitacao)

    # Testa matéria
    materia = MateriaLegislativa.objects.first()
    assert materia.numero == 165
    assert materia.ano == 2002

    return materia


@pytest.mark.django_db(transaction=False)
def test_materia_anexada_submit(admin_client):
    materia_principal = make_materia_principal()

    # Cria a matéria que será anexada
    tipo_anexada = mommy.make(TipoMateriaLegislativa,
                              sigla='T2',
                              descricao='Teste_2')
    regime_tramitacao = mommy.make(RegimeTramitacao, descricao='Teste_Regime')
    mommy.make(MateriaLegislativa,
               tipo=tipo_anexada,
               numero='32',
               ano='2004',
               data_apresentacao='2005-11-10',
               regime_tramitacao=regime_tramitacao)

    # Testa se a matéria que será anexada foi criada
    materia_anexada = MateriaLegislativa.objects.get(numero=32, ano=2004)

    # Testa POST
    response = admin_client.post(reverse('sapl.materia:anexada_create',
                                         kwargs={'pk': materia_principal.pk}),
                                 {'tipo': materia_anexada.tipo.pk,
                                  'numero': materia_anexada.numero,
                                  'ano': materia_anexada.ano,
                                  'data_anexacao': '2016-03-18',
                                  'salvar': 'salvar'},
                                 follow=True)
    assert response.status_code == 200

    # Verifica se a matéria foi anexada corretamente
    anexada = Anexada.objects.first()
    assert anexada.materia_principal == materia_principal
    assert anexada.materia_anexada == materia_anexada


@pytest.mark.django_db(transaction=False)
def test_autoria_submit(admin_client):
    materia_principal = make_materia_principal()
    # Cria um tipo de Autor
    tipo_autor = mommy.make(TipoAutor, descricao='Teste Tipo_Autor')

    # Cria um Autor
    autor = mommy.make(
        Autor,
        tipo=tipo_autor,
        nome='Autor Teste')

    # Testa POST
    response = admin_client.post(
        reverse('sapl.materia:autoria_create',
                kwargs={'pk': materia_principal.pk}),
        {'autor': autor.pk,
         'primeiro_autor': True,
         'materia_id': materia_principal.pk, },
        follow=True)
    assert response.status_code == 200

    # Verifica se o autor foi realmente criado
    autoria = Autoria.objects.first()
    assert autoria.autor == autor
    assert autoria.materia == materia_principal
    assert autoria.primeiro_autor is True


@pytest.mark.django_db(transaction=False)
def test_despacho_inicial_submit(admin_client):
    materia_principal = make_materia_principal()

    # Cria uma comissão
    tipo_comissao = mommy.make(TipoComissao)
    comissao = mommy.make(Comissao,
                          tipo=tipo_comissao,
                          nome='Teste',
                          ativa=True,
                          sigla='T',
                          data_criacao='2016-03-18')

    # Testa POST
    response = admin_client.post(reverse('sapl.materia:despachoinicial_create',
                                         kwargs={'pk': materia_principal.pk}),
                                 {'comissao': comissao.pk,
                                  'salvar': 'salvar'},
                                 follow=True)
    assert response.status_code == 200

    # Verifica se o despacho foi criado
    despacho = DespachoInicial.objects.first()

    assert despacho.comissao == comissao
    assert despacho.materia == materia_principal


@pytest.mark.django_db(transaction=False)
def test_numeracao_submit(admin_client):
    materia_principal = make_materia_principal()
    materia = make_materia_principal()

    # Testa POST
    response = admin_client.post(reverse('sapl.materia:numeracao_create',
                                         kwargs={'pk': materia_principal.pk}),
                                 {'tipo_materia': materia.tipo.pk,
                                  'numero_materia': materia.numero,
                                  'ano_materia': materia.ano,
                                  'data_materia': '2016-03-21',
                                  'salvar': 'salvar'},
                                 follow=True)

    assert response.status_code == 200

    # Verifica se a numeração foi criada
    numeracao = Numeracao.objects.first()
    assert numeracao.tipo_materia == materia.tipo
    assert numeracao.ano_materia == materia.ano


@pytest.mark.django_db(transaction=False)
def test_documento_acessorio_submit(admin_client):
    materia_principal = make_materia_principal()

    # Cria um tipo de Autor
    tipo_autor = mommy.make(TipoAutor, descricao='Teste Tipo_Autor')

    # Cria um Autor
    autor = mommy.make(
        Autor,
        tipo=tipo_autor,
        nome='Autor Teste')

    # Cria um tipo de documento
    tipo = mommy.make(TipoDocumento,
                      descricao='Teste')

    # Testa POST
    response = admin_client.post(reverse(
        'sapl.materia:documentoacessorio_create',
        kwargs={'pk': materia_principal.pk}),
        {'tipo': tipo.pk,
         'nome': 'teste_nome',
         'data_materia': '2016-03-21',
         'autor': autor,
         'ementa': 'teste_ementa',
         'data': '2016-03-21',
         'salvar': 'salvar'},
        follow=True)

    assert response.status_code == 200

    # Verifica se o documento foi criado
    doc = DocumentoAcessorio.objects.first()
    assert doc.tipo == tipo
    assert doc.nome == 'teste_nome'
    assert doc.autor == str(autor)


@pytest.mark.django_db(transaction=False)
def test_legislacao_citada_submit(admin_client):
    materia_principal = make_materia_principal()
    norma = make_norma()

    # Testa POST
    response = admin_client.post(
        reverse('sapl.materia:legislacaocitada_create',
                kwargs={'pk': materia_principal.pk}),
        {'tipo': norma.tipo.pk,
         'numero': norma.numero,
         'ano': norma.ano,
         'disposicao': 'disposicao',
         'salvar': 'salvar'},
        follow=True)

    assert response.status_code == 200

    # Testa se a legislação citada foi criada
    leg = LegislacaoCitada.objects.first()
    assert leg.norma == norma


@pytest.mark.django_db(transaction=False)
def test_tramitacao_submit(admin_client):
    materia_principal = make_materia_principal()
    # Cria status para tramitação
    status_tramitacao = mommy.make(StatusTramitacao,
                                   indicador='F',
                                   sigla='ST',
                                   descricao='Status_Teste')
    # Testa POST
    response = admin_client.post(
        reverse('sapl.materia:tramitacao_create',
                kwargs={'pk': materia_principal.pk}),
        {'unidade_tramitacao_local': make_unidade_tramitacao(
            'Unidade Local').pk,
         'unidade_tramitacao_destino': make_unidade_tramitacao(
            'Unidade Destino').pk,
         'urgente': True,
         'status': status_tramitacao.pk,
         'data_tramitacao': '2016-03-21',
         'data_fim_prazo': '2016-03-22',
         'data_encaminhamento': '2016-03-22',
         'texto': 'Texto_Teste',
         'salvar': 'salvar'},
        follow=True)

    assert response.status_code == 200

    # Testa se a tramitacao foi criada
    tramitacao = Tramitacao.objects.first()
    assert (tramitacao.unidade_tramitacao_local.comissao.nome ==
            'Unidade Local')
    assert (tramitacao.unidade_tramitacao_destino.comissao.nome ==
            'Unidade Destino')
    assert tramitacao.urgente is True


@pytest.mark.django_db(transaction=False)
def test_form_errors_anexada(admin_client):
    materia_principal = make_materia_principal()
    response = admin_client.post(reverse('sapl.materia:anexada_create',
                                         kwargs={'pk': materia_principal.pk}),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['tipo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['numero'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['ano'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data_anexacao'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_autoria(admin_client):
    materia_principal = make_materia_principal()

    response = admin_client.post(reverse('sapl.materia:autoria_create',
                                         kwargs={'pk': materia_principal.pk}),
                                 {'materia_id': materia_principal.pk,
                                  'autor_id': '', },
                                 follow=True)

    assert (response.context_data['form'].errors['autor'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_despacho_inicial(admin_client):
    materia_principal = make_materia_principal()

    response = admin_client.post(reverse('sapl.materia:despachoinicial_create',
                                         kwargs={'pk': materia_principal.pk}),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['comissao'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_documento_acessorio(admin_client):
    materia_principal = make_materia_principal()

    response = admin_client.post(
        reverse('sapl.materia:documentoacessorio_create',
                kwargs={'pk': materia_principal.pk}),
        {'salvar': 'salvar'},
        follow=True)

    assert (response.context_data['form'].errors['tipo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['nome'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_legislacao_citada(admin_client):
    materia_principal = make_materia_principal()

    response = admin_client.post(
        reverse('sapl.materia:legislacaocitada_create',
                kwargs={'pk': materia_principal.pk}),
        {'salvar': 'salvar'},
        follow=True)

    assert (response.context_data['form'].errors['tipo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['numero'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['ano'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_numeracao(admin_client):
    materia_principal = make_materia_principal()

    response = admin_client.post(reverse('sapl.materia:numeracao_create',
                                         kwargs={'pk': materia_principal.pk}),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['tipo_materia'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['numero_materia'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['ano_materia'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data_materia'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_tramitacao(admin_client):
    materia_principal = make_materia_principal()

    response = admin_client.post(
        reverse('sapl.materia:tramitacao_create',
                kwargs={'pk': materia_principal.pk}),
        {'salvar': 'salvar'},
        follow=True)

    assert (response.context_data['form'].errors['data_tramitacao'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors[
            'unidade_tramitacao_local'] == ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['status'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors[
            'unidade_tramitacao_destino'] == ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['texto'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_relatoria(admin_client):
    materia_principal = make_materia_principal()

    response = admin_client.post(
        reverse('sapl.materia:relatoria_create',
                kwargs={'pk': materia_principal.pk}),
        {'salvar': 'salvar'},
        follow=True)

    assert (response.context_data['form'].errors['data_designacao_relator'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['parlamentar'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_proposicao_submit(admin_client):
    tipo_autor = mommy.make(TipoAutor, descricao='Teste Tipo_Autor')
    user = get_user_model().objects.filter(is_active=True)[0]

    autor = mommy.make(
        Autor,
        user=user,
        tipo=tipo_autor,
        nome='Autor Teste')

    file_content = 'file_content'
    texto = SimpleUploadedFile("file.txt", file_content.encode('UTF-8'))

    mcts = ContentType.objects.get_for_models(
        *models_with_gr_for_model(TipoProposicao))

    for pk, mct in enumerate(mcts):
        tipo_conteudo_related = mommy.make(mct, pk=pk + 1)

        response = admin_client.post(
            reverse('sapl.materia:proposicao_create'),
            {'tipo': mommy.make(
                TipoProposicao, pk=3,
                tipo_conteudo_related=tipo_conteudo_related).pk,
             'descricao': 'Teste proposição',
             'justificativa_devolucao': '  ',
             'status': 'E',
             'autor': autor.pk,
             'texto_original': texto,
             'salvar': 'salvar',
             },
            follow=True)

        assert response.status_code == 200

        proposicao = Proposicao.objects.first()

        assert proposicao is not None
        assert proposicao.descricao == 'Teste proposição'
        assert proposicao.tipo.pk == 3
        assert proposicao.tipo.tipo_conteudo_related.pk == pk + 1


@pytest.mark.django_db(transaction=False)
def test_form_errors_proposicao(admin_client):
    tipo_autor = mommy.make(TipoAutor, descricao='Teste Tipo_Autor')

    user = get_user_model().objects.filter(is_active=True)[0]

    autor = mommy.make(
        Autor,
        user=user,
        tipo=tipo_autor,
        nome='Autor Teste')

    file_content = 'file_content'
    texto = SimpleUploadedFile("file.txt", file_content.encode('UTF-8'))

    response = admin_client.post(reverse('sapl.materia:proposicao_create'),
                                 {'autor': autor.pk,
                                  'justificativa_devolucao': '  ',
                                  'texto_original': texto,
                                  'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['tipo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['descricao'] ==
            ['Este campo é obrigatório.'])
