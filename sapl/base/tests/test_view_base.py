import pytest
from model_mommy import mommy
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import Autor, TipoAutor
from sapl.comissoes.models import Comissao, TipoComissao
from sapl.sessao.models import Bancada
from sapl.protocoloadm.models import Protocolo
from sapl.materia.models import (TipoMateriaLegislativa, RegimeTramitacao,
                                 MateriaLegislativa)
from sapl.parlamentares.models import (Parlamentar, Partido, Filiacao,
                                       Legislatura, Mandato)

from sapl.base.views import (protocolos_duplicados, protocolos_com_materias,
                             materias_protocolo_inexistente,
                             mandato_sem_data_inicio, parlamentares_duplicados,
                             parlamentares_mandatos_intersecao,
                             parlamentares_filiacoes_intersecao,
                             autores_duplicados,
                             bancada_comissao_autor_externo)


@pytest.mark.django_db(transaction=False)
def test_lista_protocolos_duplicados():
        mommy.make(
                Protocolo,
                numero=15,
                ano=2031
        )
        mommy.make(
                Protocolo,
                numero=15,
                ano=2031
        )
        mommy.make(
                Protocolo,
                numero=33,
                ano=2033
        )

        lista_protocolos_duplicados = protocolos_duplicados()

        assert len(lista_protocolos_duplicados) == 1
        assert lista_protocolos_duplicados[0][1] == 2
        assert lista_protocolos_duplicados[0][0].numero == 15
        assert lista_protocolos_duplicados[0][0].ano == 2031


@pytest.mark.django_db(transaction=False)
def test_lista_protocolos_com_materias():
        mommy.make(
                Protocolo,
                numero=15,
                ano=2035
        )
        mommy.make(
                Protocolo,
                numero=33,
                ano=2035
        )

        tipo_materia = mommy.make(
                TipoMateriaLegislativa,
                descricao="Tipo_Materia_Teste"
        )
        regime_tramitacao = mommy.make(
                RegimeTramitacao,
                descricao="Regime_Tramitacao_Teste"
        )
        mommy.make(
                MateriaLegislativa,
                numero=16,
                ano=2035,
                data_apresentacao='2035-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )
        mommy.make(
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
        protocolo_a = mommy.make(
                Protocolo,
                numero=15,
                ano=2031
        )

        tipo_materia = mommy.make(
                TipoMateriaLegislativa,
                descricao="Tipo_Materia_Teste"
        )
        regime_tramitacao = mommy.make(
                RegimeTramitacao,
                descricao="Regime_Tramitacao_Teste"
        )
        mommy.make(
                MateriaLegislativa,
                numero=16,
                ano=2031,
                data_apresentacao='2031-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )
        materia = mommy.make(
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
        parlamentar = mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        legislatura = mommy.make(
                Legislatura,
                numero=1,
                data_inicio='2015-05-02',
                data_fim='2024-02-04',
                data_eleicao='2015-02-05'
        )

        mandato_a = mommy.make(
                Mandato,
                parlamentar=parlamentar,
                legislatura=legislatura
        )
        mommy.make(
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
        mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste-1",
                nome_parlamentar="Nome_Parlamentar_Teste-1",
                sexo='M'
        )

        lista_dict_values_parlamentares_duplicados = parlamentares_duplicados()
        parlamentar_duplicado = list(
                lista_dict_values_parlamentares_duplicados[0]
        )
        parlamentar_duplicado.sort(key=str)

        assert len(lista_dict_values_parlamentares_duplicados) == 1
        assert parlamentar_duplicado == [2, "Nome_Parlamentar_Teste"]


@pytest.mark.django_db(transaction=False)
def test_lista_parlamentares_mandatos_intersecao():
        legislatura = mommy.make(
                Legislatura,
                numero=1,
                data_inicio='2017-07-04',
                data_fim='2170-05-01',
                data_eleicao='2017-04-07'
        )
        parlamentar_a = mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        parlamentar_b = mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste-1",
                nome_parlamentar="Nome_Parlamentar_Teste-1",
                sexo='M'
        )

        mandato_a = mommy.make(
                Mandato,
                parlamentar=parlamentar_a,
                legislatura=legislatura,
                data_inicio_mandato='2017-07-08',
                data_fim_mandato='2018-01-07'
        )
        mandato_b = mommy.make(
                Mandato,
                parlamentar=parlamentar_a,
                legislatura=legislatura,
                data_inicio_mandato='2017-07-09'
        )
        mommy.make(
                Mandato,
                parlamentar=parlamentar_b,
                legislatura=legislatura,
                data_inicio_mandato='2017-11-17',
                data_fim_mandato='2018-08-02'
        )
        mommy.make(
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
        partido = mommy.make(
                Partido,
                sigla="ST",
                nome="Nome_Partido_Teste"
        )
        parlamentar_a = mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste",
                nome_parlamentar="Nome_Parlamentar_Teste",
                sexo='M'
        )
        parlamentar_b = mommy.make(
                Parlamentar,
                nome_completo="Nome_Completo_Parlamentar_Teste-1",
                nome_parlamentar="Nome_Parlamentar_Teste-1",
                sexo='M'
        )

        filiacao_a = mommy.make(
                Filiacao,
                parlamentar=parlamentar_a,
                partido=partido,
                data='2018-02-02',
                data_desfiliacao='2019-08-01'
        )
        filiacao_b = mommy.make(
                Filiacao,
                parlamentar=parlamentar_a,
                partido=partido,
                data='2018-02-23',
                data_desfiliacao='2020-02-04'
        )
        mommy.make(
                Filiacao,
                parlamentar=parlamentar_b,
                partido=partido,
                data='2018-02-07',
                data_desfiliacao='2018-02-27'
        )
        mommy.make(
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
        tipo_autor = mommy.make(
                TipoAutor,
                descricao="Tipo_Autor_Teste"
        )

        mommy.make(
                Autor,
                tipo=tipo_autor,
                nome="Nome_Autor_Teste"
        )
        mommy.make(
                Autor,
                tipo=tipo_autor,
                nome="Nome_Autor_Teste"
        )
        mommy.make(
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
        tipo_autor = mommy.make(
                TipoAutor,
                descricao="Tipo_Autor_Teste"
        )
        tipo_autor_externo = mommy.make(
                TipoAutor,
                descricao="Externo"
        )

        legislatura = mommy.make(
                Legislatura,
                numero=1,
                data_inicio='2012-01-03',
                data_fim='2013-01-02',
                data_eleicao='2011-10-04'
        )

        bancada_a = mommy.make(
                Bancada,
                legislatura=legislatura,
                nome="Bancada_Teste",
                data_criacao='2012-01-08',
        )
        bancada_a.autor.create(
                nome="Nome_Autor_Teste",
                tipo=tipo_autor
        )

        bancada_b = mommy.make(
                Bancada,
                legislatura=legislatura,
                nome="Bancada_Teste-1",
                data_criacao='2012-02-02'
        )
        autor_bancada_b = bancada_b.autor.create(
                nome="Nome_Autor_Externo_Teste",
                tipo=tipo_autor_externo
        )

        tipo_comissao = mommy.make(
                TipoComissao,
                nome="Tipo_Comissao_Teste",
                natureza='T',
                sigla="TCT"
        )

        comissao_a = mommy.make(
                Comissao,
                nome="Comissao_Teste",
                sigla="CT",
                data_criacao='2012-03-08',
        )
        comissao_a.autor.create(
                nome="Nome_Autor_Teste",
                tipo=tipo_autor
        )

        comissao_b = mommy.make(
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
