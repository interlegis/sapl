import pytest
from model_bakery import baker
import datetime
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from model_bakery import baker

from sapl.base.models import Autor, TipoAutor
from sapl.comissoes.models import Comissao, TipoComissao
from sapl.sessao.models import Bancada
from sapl.protocoloadm.models import (Protocolo, DocumentoAdministrativo,
                                      TipoDocumentoAdministrativo, Anexado)
from sapl.materia.models import (TipoMateriaLegislativa, RegimeTramitacao,
                                 MateriaLegislativa, Anexada)
from sapl.parlamentares.models import (Parlamentar, Partido, Filiacao,
                                       Legislatura, Mandato)

from sapl.base.views import (protocolos_duplicados, protocolos_com_materias,
                             materias_protocolo_inexistente,
                             mandato_sem_data_inicio, parlamentares_duplicados,
                             parlamentares_mandatos_intersecao,
                             parlamentares_filiacoes_intersecao,
                             autores_duplicados,
                             bancada_comissao_autor_externo, anexados_ciclicos)


@pytest.mark.django_db(transaction=False)
def test_lista_protocolos_com_materias():
        baker.make(
                Protocolo,
                numero=15,
                ano=2035
        )
        baker.make(
                Protocolo,
                numero=33,
                ano=2035
        )

        tipo_materia = baker.make(
                TipoMateriaLegislativa,
                descricao="Tipo_Materia_Teste"
        )
        regime_tramitacao = baker.make(
                RegimeTramitacao,
                descricao="Regime_Tramitacao_Teste"
        )
        baker.make(
                MateriaLegislativa,
                numero=16,
                ano=2035,
                data_apresentacao='2035-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )
        baker.make(
                MateriaLegislativa,
                numero=17,
                ano=2035,
                data_apresentacao='2035-06-05',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )

        lista_protocolos_com_materias = protocolos_com_materias()

        assert len(lista_protocolos_com_materias) == 1
        assert lista_protocolos_com_materias[0][1] == 2
        assert lista_protocolos_com_materias[0][0].numero_protocolo == 15
        assert lista_protocolos_com_materias[0][0].ano == 2035


@pytest.mark.django_db(transaction=False)
def test_lista_materias_protocolo_inexistente():
        protocolo_a = baker.make(
                Protocolo,
                numero=15,
                ano=2031
        )

        tipo_materia = baker.make(
                TipoMateriaLegislativa,
                descricao="Tipo_Materia_Teste"
        )
        regime_tramitacao = baker.make(
                RegimeTramitacao,
                descricao="Regime_Tramitacao_Teste"
        )
        baker.make(
                MateriaLegislativa,
                numero=16,
                ano=2031,
                data_apresentacao='2031-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )
        materia = baker.make(
                MateriaLegislativa,
                numero=17,
                ano=2031,
                data_apresentacao='2031-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=16
        )

        lista_materias_protocolo_inexistente = materias_protocolo_inexistente()

        assert len(lista_materias_protocolo_inexistente) == 1
        assert lista_materias_protocolo_inexistente == [(materia, 2031, 16)]


@pytest.mark.django_db(transaction=False)
def test_lista_mandatos_sem_data_inicio():
        parlamentar = baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        legislatura = baker.make(
                Legislatura,
                numero=1,
                data_inicio='2015-05-02',
                data_fim='2024-02-04',
                data_eleicao='2015-02-05'
        )

        mandato_a = baker.make(
                Mandato,
                parlamentar=parlamentar,
                legislatura=legislatura
        )
        baker.make(
                Mandato,
                parlamentar=parlamentar,
                legislatura=legislatura,
                data_inicio_mandato='2015-05-27'
        )

        lista_mandatos_sem_data_inicio = mandato_sem_data_inicio()

        assert len(lista_mandatos_sem_data_inicio) == 1
        assert lista_mandatos_sem_data_inicio[0] == mandato_a


@pytest.mark.django_db(transaction=False)
def test_lista_parlamentares_duplicados():
        baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste-1",
                nome_parlamentar="Nome_Parlamentar_Teste-1",
                sexo='M'
        )

        lista_dict_parlamentares_duplicados = parlamentares_duplicados()
        parlamentar_duplicado = list(
                lista_dict_parlamentares_duplicados[0].values()
        )
        parlamentar_duplicado.sort(key=str)

        assert len(lista_dict_parlamentares_duplicados) == 1
        assert parlamentar_duplicado == [2, "Nome_Parlamentar_Teste"]


@pytest.mark.django_db(transaction=False)
def test_lista_parlamentares_mandatos_intersecao():
        legislatura = baker.make(
                Legislatura,
                numero=1,
                data_inicio='2017-07-04',
                data_fim='2170-05-01',
                data_eleicao='2017-04-07'
        )
        parlamentar_a = baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        parlamentar_b = baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste-1",
                nome_parlamentar="Nome_Parlamentar_Teste-1",
                sexo='M'
        )

        mandato_a = baker.make(
                Mandato,
                parlamentar=parlamentar_a,
                legislatura=legislatura,
                data_inicio_mandato='2017-07-08',
                data_fim_mandato='2018-01-07'
        )
        mandato_b = baker.make(
                Mandato,
                parlamentar=parlamentar_a,
                legislatura=legislatura,
                data_inicio_mandato='2017-07-09'
        )
        baker.make(
                Mandato,
                parlamentar=parlamentar_b,
                legislatura=legislatura,
                data_inicio_mandato='2017-11-17',
                data_fim_mandato='2018-08-02'
        )
        baker.make(
                Mandato,
                parlamentar=parlamentar_b,
                legislatura=legislatura,
                data_inicio_mandato='2018-08-03'
        )

        lista_parlamentares = parlamentares_mandatos_intersecao()

        assert len(lista_parlamentares) == 1
        assert lista_parlamentares == [(parlamentar_a, mandato_a, mandato_b)]


@pytest.mark.django_db(transaction=False)
def test_lista_parlamentares_filiacoes_intersecao():
        partido = baker.make(
                Partido,
                sigla="ST",
                nome="Nome_Partido_Teste"
        )
        parlamentar_a = baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        parlamentar_b = baker.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste-1",
                nome_parlamentar="Nome_Parlamentar_Teste-1",
                sexo='M'
        )

        filiacao_a = baker.make(
                Filiacao,
                parlamentar=parlamentar_a,
                partido=partido,
                data='2018-02-02',
                data_desfiliacao='2019-08-01'
        )
        filiacao_b = baker.make(
                Filiacao,
                parlamentar=parlamentar_a,
                partido=partido,
                data='2018-02-23',
                data_desfiliacao='2020-02-04'
        )
        baker.make(
                Filiacao,
                parlamentar=parlamentar_b,
                partido=partido,
                data='2018-02-07',
                data_desfiliacao='2018-02-27'
        )
        baker.make(
                Filiacao,
                parlamentar=parlamentar_b,
                partido=partido,
                data='2018-02-28'
        )

        lista_parlamentares = parlamentares_filiacoes_intersecao()

        assert len(lista_parlamentares) == 1
        assert lista_parlamentares == [(parlamentar_a, filiacao_b, filiacao_a)]


@pytest.mark.django_db(transaction=False)
def test_lista_autores_duplicados():
        tipo_autor = baker.make(
                TipoAutor,
                descricao="Tipo_Autor_Teste"
        )

        baker.make(
                Autor,
                tipo=tipo_autor,
                nome="Nome_Autor_Teste"
        )
        baker.make(
                Autor,
                tipo=tipo_autor,
                nome="Nome_Autor_Teste"
        )
        baker.make(
                Autor,
                tipo=tipo_autor,
                nome="Nome_Autor_Teste-1"
        )

        lista_autores_duplicados = autores_duplicados()

        assert len(lista_autores_duplicados) == 1
        assert lista_autores_duplicados[0]['count'] == 2
        assert lista_autores_duplicados[0]['nome'] == "Nome_Autor_Teste"


@pytest.mark.django_db(transaction=False)
def test_lista_bancada_comissao_autor_externo():
        tipo_autor = baker.make(
                TipoAutor,
                descricao="Tipo_Autor_Teste"
        )
        tipo_autor_externo = baker.make(
                TipoAutor,
                descricao="Externo"
        )

        legislatura = baker.make(
                Legislatura,
                numero=1,
                data_inicio='2012-01-03',
                data_fim='2013-01-02',
                data_eleicao='2011-10-04'
        )

        bancada_a = baker.make(
                Bancada,
                legislatura=legislatura,
                nome="Bancada_Teste",
                data_criacao='2012-01-08',
        )
        bancada_a.autor.create(
                nome="Nome_Autor_Teste",
                tipo=tipo_autor
        )

        bancada_b = baker.make(
                Bancada,
                legislatura=legislatura,
                nome="Bancada_Teste-1",
                data_criacao='2012-02-02'
        )
        autor_bancada_b = bancada_b.autor.create(
                nome="Nome_Autor_Externo_Teste",
                tipo=tipo_autor_externo
        )

        tipo_comissao = baker.make(
                TipoComissao,
                nome="Tipo_Comissao_Teste",
                natureza='T',
                sigla="TCT"
        )

        comissao_a = baker.make(
                Comissao,
                nome="Comissao_Teste",
                sigla="CT",
                data_criacao='2012-03-08',
        )
        comissao_a.autor.create(
                nome="Nome_Autor_Teste",
                tipo=tipo_autor
        )

        comissao_b = baker.make(
                Comissao,
                nome="Comissao_Teste-1",
                sigla="CT1",
                data_criacao='2012-04-01',
        )
        autor_comissao_b = comissao_b.autor.create(
                nome="Nome_Autor_Externo_Teste",
                tipo=tipo_autor_externo
        )

        lista_bancada_comissao = bancada_comissao_autor_externo()

        assert len(lista_bancada_comissao) == 2
        assert lista_bancada_comissao[0][0:2] == (autor_bancada_b, bancada_b)
        assert lista_bancada_comissao[0][2:4] == ('Bancada', 'sistema/bancada')
        assert lista_bancada_comissao[1][0:2] == (autor_comissao_b, comissao_b)
        assert lista_bancada_comissao[1][2:4] == ('Comissão', 'comissao')


@pytest.mark.django_db(transaction=False)
def test_lista_anexados_ciclicas():
        ## DocumentoAdministrativo
        tipo_documento = baker.make(
                TipoDocumentoAdministrativo,
                sigla="TT",
                descricao="Tipo_Teste"
        )
        
        documento_a = baker.make(
                DocumentoAdministrativo,
                tipo=tipo_documento,
                numero=26,
                ano=2019,
                data='2019-05-15',
        )
        documento_b = baker.make(
                DocumentoAdministrativo,
                tipo=tipo_documento,
                numero=27,
                ano=2019,
                data='2019-05-16',
        )
        documento_c = baker.make(
                DocumentoAdministrativo,
                tipo=tipo_documento,
                numero=28,
                ano=2019,
                data='2019-05-17',
        )
        documento_a1 = baker.make(
                DocumentoAdministrativo,
                tipo=tipo_documento,
                numero=29,
                ano=2019,
                data='2019-05-18',
        )
        documento_b1 = baker.make(
                DocumentoAdministrativo,
                tipo=tipo_documento,
                numero=30,
                ano=2019,
                data='2019-05-19',
        )
        documento_c1 = baker.make(
                DocumentoAdministrativo,
                tipo=tipo_documento,
                numero=31,
                ano=2019,
                data='2019-05-20',
        )

        baker.make(
                Anexado,
                documento_principal=documento_a,
                documento_anexado=documento_b,
                data_anexacao='2019-05-21'
        )
        baker.make(
                Anexado,
                documento_principal=documento_a,
                documento_anexado=documento_c,
                data_anexacao='2019-05-22'
        )
        baker.make(
                Anexado,
                documento_principal=documento_b,
                documento_anexado=documento_c,
                data_anexacao='2019-05-23'
        )
        baker.make(
                Anexado,
                documento_principal=documento_a1,
                documento_anexado=documento_b1,
                data_anexacao='2019-05-24'
        )
        baker.make(
                Anexado,
                documento_principal=documento_a1,
                documento_anexado=documento_c1,
                data_anexacao='2019-05-25'
        )
        baker.make(
                Anexado,
                documento_principal=documento_b1,
                documento_anexado=documento_c1,
                data_anexacao='2019-05-26'
        )
        baker.make(
                Anexado,
                documento_principal=documento_c1,
                documento_anexado=documento_b1,
                data_anexacao='2019-05-27'
        )

        lista_documento_ciclicos = anexados_ciclicos(False)

        ## Matéria
        tipo_materia = baker.make(
                TipoMateriaLegislativa,
                descricao="Tipo_Teste"
        )
        regime_tramitacao = baker.make(
                RegimeTramitacao,
                descricao="Regime_Teste"
        )

        materia_a = baker.make(
                MateriaLegislativa,
                numero=20,
                ano=2018,
                data_apresentacao="2018-01-04",
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia
        )
        materia_b = baker.make(
                MateriaLegislativa,
                numero=21,
                ano=2019,
                data_apresentacao="2019-05-04",
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia
        )
        materia_c = baker.make(
                MateriaLegislativa,
                numero=22,
                ano=2019,
                data_apresentacao="2019-05-05",
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia
        )
        materia_a1 = baker.make(
                MateriaLegislativa,
                numero=23,
                ano=2018,
                data_apresentacao="2019-05-06",
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia
        )
        materia_b1 = baker.make(
                MateriaLegislativa,
                numero=24,
                ano=2019,
                data_apresentacao="2019-05-07",
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia
        )
        materia_c1 = baker.make(
                MateriaLegislativa,
                numero=25,
                ano=2019,
                data_apresentacao="2019-05-08",
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia
        ) 

        baker.make(
                Anexada,
                materia_principal=materia_a,
                materia_anexada=materia_b,
                data_anexacao='2019-05-11'
        )
        baker.make(
                Anexada,
                materia_principal=materia_a,
                materia_anexada=materia_c,
                data_anexacao='2019-05-12'
        )
        baker.make(
                Anexada,
                materia_principal=materia_b,
                materia_anexada=materia_c,
                data_anexacao='2019-05-13'
        )
        baker.make(
                Anexada,
                materia_principal=materia_a1,
                materia_anexada=materia_b1,
                data_anexacao='2019-05-11'
        )
        baker.make(
                Anexada,
                materia_principal=materia_a1,
                materia_anexada=materia_c1,
                data_anexacao='2019-05-12'
        )
        baker.make(
                Anexada,
                materia_principal=materia_b1,
                materia_anexada=materia_c1,
                data_anexacao='2019-05-13'
        )
        baker.make(
                Anexada,
                materia_principal=materia_c1,
                materia_anexada=materia_b1,
                data_anexacao='2019-05-14'
        )

        lista_materias_ciclicas = anexados_ciclicos(True)

        assert len(lista_materias_ciclicas) == 2
        assert lista_materias_ciclicas[0] == (datetime.date(2019,5,13), materia_b1, materia_c1)
        assert lista_materias_ciclicas[1] == (datetime.date(2019,5,14), materia_c1, materia_b1)

        assert len(lista_documento_ciclicos) == 2
        assert lista_documento_ciclicos[0] == (datetime.date(2019,5,26), documento_b1, documento_c1)
        assert lista_documento_ciclicos[1] == (datetime.date(2019,5,27), documento_c1, documento_b1)


@pytest.mark.django_db(transaction=False)
def test_incluir_casa_legislativa_errors(admin_client):

    response = admin_client.post(reverse('sapl.base:casalegislativa_create'),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['nome'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['sigla'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['endereco'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['cep'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['municipio'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['uf'] ==
            [_('Este campo é obrigatório.')])


@pytest.mark.django_db(transaction=False)
def test_incluir_tipo_autor_errors(admin_client):

    response = admin_client.post(reverse('sapl.base:tipoautor_create'),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['descricao'] ==
            [_('Este campo é obrigatório.')])
