import pytest
from model_bakery import baker

from sapl.base.models import CasaLegislativa
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
