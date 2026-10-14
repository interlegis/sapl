from datetime import date

import pytest
from django.urls import reverse
from model_bakery import baker

from sapl.base.models import Autor, CasaLegislativa
from sapl.materia.models import Autoria, MateriaLegislativa
from sapl.norma.models import AutoriaNorma, NormaJuridica
from sapl.relatorios import views as relatorios_views
from sapl.relatorios.views import get_sessao_plenaria
from sapl.sessao.models import ExpedienteSessao, SessaoPlenaria, TipoExpediente
from sapl.sessao.views import get_expedientes


def cria_sessao_com_expedientes():
    """Cria uma sessão cujos expedientes têm `ordenacao` inversa à ordem
    alfabética dos nomes -- o caso que expõe o OSTicket #125461."""
    sessao = baker.make(SessaoPlenaria)
    tipo_leitura = baker.make(
        TipoExpediente, nome='Leitura e Aprovação da Ata', ordenacao=1)
    tipo_grande = baker.make(
        TipoExpediente, nome='Grande Expediente', ordenacao=2)

    for tipo in (tipo_grande, tipo_leitura):
        baker.make(ExpedienteSessao, sessao_plenaria=sessao, tipo=tipo,
                   conteudo='<p>Conteúdo de {}.</p>'.format(tipo.nome))

    return sessao


@pytest.mark.django_db(transaction=False)
def test_relatorio_sessao_respeita_ordenacao_do_tipo_expediente():
    """O PDF da Sessão Plenária deve seguir o campo `ordenacao` de
    TipoExpediente, e não a ordem alfabética do nome."""
    sessao = cria_sessao_com_expedientes()
    casa = baker.make(CasaLegislativa)
    user = baker.make('auth.User')

    lst_expedientes = get_sessao_plenaria(sessao, casa, user)[6]
    nomes = [e['nom_expediente'] for e in lst_expedientes]

    assert nomes == ['Leitura e Aprovação da Ata', 'Grande Expediente']


@pytest.mark.django_db(transaction=False)
def test_relatorio_sessao_tem_mesma_ordem_de_expedientes_do_resumo():
    """O PDF e o Resumo exibido em tela não podem divergir: foi essa
    divergência que originou o OSTicket #125461."""
    sessao = cria_sessao_com_expedientes()
    casa = baker.make(CasaLegislativa)
    user = baker.make('auth.User')

    do_pdf = [e['nom_expediente']
              for e in get_sessao_plenaria(sessao, casa, user)[6]]
    da_tela = [e['tipo'].nome for e in get_expedientes(sessao)['expedientes']]

    assert do_pdf == da_tela


MSG_AUTOR_OU_PERIODO = 'Selecione um autor ou informe o período'


def params_materias_por_autor(autor='', inicio='', fim='', **extra):
    return dict(tipo='', data_apresentacao_0=inicio,
                data_apresentacao_1=fim, autoria__autor=autor,
                pesquisar='Pesquisar', **extra)


def params_normas_por_autor(autor='', inicio='', fim='', **extra):
    return dict(tipo='', data_0=inicio, data_1=fim,
                autorianorma__autor=autor, pesquisar='Pesquisar', **extra)


def cria_materia(numero, data_apresentacao, autores):
    materia = baker.make(MateriaLegislativa, numero=numero,
                         ano=data_apresentacao.year,
                         data_apresentacao=data_apresentacao,
                         ementa='Ementa da matéria {}'.format(numero))
    for i, autor in enumerate(autores):
        baker.make(Autoria, materia=materia, autor=autor,
                   primeiro_autor=(i == 0))
    return materia


def cria_norma(numero, data_norma, autores):
    norma = baker.make(NormaJuridica, numero=numero, ano=data_norma.year,
                       data=data_norma,
                       ementa='Ementa da norma {}'.format(numero))
    for i, autor in enumerate(autores):
        baker.make(AutoriaNorma, norma=norma, autor=autor,
                   primeiro_autor=(i == 0))
    return norma


@pytest.fixture
def pdf_html(monkeypatch):
    """Troca o WeasyPrint por uma captura do HTML que iria para o PDF."""
    baker.make(CasaLegislativa, cep='')
    capturado = {}

    def make_pdf(base_url, main_template, header_template, **kwargs):
        capturado['html'] = main_template
        return b'%PDF-fake'

    monkeypatch.setattr(relatorios_views, 'make_pdf', make_pdf)
    return capturado


@pytest.mark.django_db(transaction=False)
def test_materias_por_autor_sem_autor_e_sem_periodo_pede_filtro(client):
    response = client.get(reverse('sapl.relatorios:materia_por_autor'),
                          params_materias_por_autor())

    assert MSG_AUTOR_OU_PERIODO in response.content.decode()
    assert not response.context.get('show_results')


@pytest.mark.django_db(transaction=False)
def test_materias_por_autor_sem_autor_lista_materias_do_periodo(client):
    """OSTicket #885134: sem autor, a pesquisa por período deve listar as
    matérias do período, uma vez cada, mesmo as de mais de um autor."""
    ana = baker.make(Autor, nome='Ana')
    bruno = baker.make(Autor, nome='Bruno')
    m1 = cria_materia(1, date(2025, 3, 1), [ana, bruno])
    m2 = cria_materia(2, date(2025, 6, 1), [bruno])
    cria_materia(3, date(2024, 1, 1), [ana])

    response = client.get(
        reverse('sapl.relatorios:materia_por_autor'),
        params_materias_por_autor(inicio='01/01/2025', fim='31/12/2025'))

    assert list(response.context['object_list']) == [m2, m1]
    content = response.content.decode()
    assert 'Autor: Todos' in content
    assert 'Autor(es)' in content


@pytest.mark.django_db(transaction=False)
def test_materias_por_autor_com_autor_dispensa_periodo(client):
    ana = baker.make(Autor, nome='Ana')
    bruno = baker.make(Autor, nome='Bruno')
    m1 = cria_materia(1, date(2025, 3, 1), [ana, bruno])
    cria_materia(2, date(2025, 6, 1), [bruno])
    m3 = cria_materia(3, date(2024, 1, 1), [ana])

    response = client.get(reverse('sapl.relatorios:materia_por_autor'),
                          params_materias_por_autor(autor=ana.pk))

    assert list(response.context['object_list']) == [m1, m3]


@pytest.mark.django_db(transaction=False)
def test_materias_por_autor_pdf_lista_materias(client, pdf_html):
    """OSTicket #885134: o PDF saía "Nenhum documento encontrado" mesmo com
    a tela listando as matérias do autor."""
    ana = baker.make(Autor, nome='Ana')
    cria_materia(1, date(2025, 3, 1), [ana])

    response = client.get(
        reverse('sapl.relatorios:materia_por_autor'),
        params_materias_por_autor(autor=ana.pk, relatorio='on'))

    assert response['Content-Type'].startswith('application/pdf')
    assert 'Ementa da matéria 1' in pdf_html['html']
    assert 'Nenhum documento encontrado' not in pdf_html['html']


@pytest.mark.django_db(transaction=False)
def test_materias_por_autor_pdf_sem_filtro_volta_ao_form(client, pdf_html):
    response = client.get(
        reverse('sapl.relatorios:materia_por_autor'),
        params_materias_por_autor(relatorio='on'))

    assert response['Content-Type'].startswith('text/html')
    assert MSG_AUTOR_OU_PERIODO in response.content.decode()
    assert 'html' not in pdf_html


@pytest.mark.django_db(transaction=False)
def test_normas_por_autor_sem_autor_e_sem_periodo_pede_filtro(client):
    response = client.get(reverse('sapl.relatorios:normas_por_autor'),
                          params_normas_por_autor())

    assert MSG_AUTOR_OU_PERIODO in response.content.decode()
    assert not response.context.get('show_results')


@pytest.mark.django_db(transaction=False)
def test_normas_por_autor_sem_autor_agrupa_pelo_primeiro_autor(client):
    ana = baker.make(Autor, nome='Ana')
    bruno = baker.make(Autor, nome='Bruno')
    n1 = cria_norma('1', date(2025, 3, 1), [ana, bruno])
    n2 = cria_norma('2', date(2025, 6, 1), [bruno])
    cria_norma('3', date(2024, 1, 1), [ana])

    response = client.get(
        reverse('sapl.relatorios:normas_por_autor'),
        params_normas_por_autor(inicio='01/01/2025', fim='31/12/2025'))

    assert list(response.context['object_list']) == [n1, n2]
    content = response.content.decode()
    assert 'Autor: Todos' in content
    assert 'Autor: Ana' in content
    assert 'Autor: Bruno' in content
