import pytest
from model_bakery import baker

from sapl.crispy_layout_mixin import get_field_display
from sapl.lexml.models import LexmlProvedor
from sapl.protocoloadm.models import TramitacaoAdministrativo
from sapl.sanitize import sanitize_field, sanitize_html, sanitize_scope
from sapl.sessao.models import ExpedienteSessao


def test_plain_remove_marcacao_e_preserva_texto():
    assert sanitize_html('<script>alert(1)</script>Ciente') == 'Ciente'
    assert sanitize_html('Encaminhado <b>ao</b> setor') == \
        'Encaminhado ao setor'
    assert sanitize_html('<img src=x onerror=alert(1)>') == ''
    assert sanitize_html('<div>a</div><div>b</div>') == 'ab'


def test_plain_escapa_caracteres_especiais():
    assert sanitize_html('Valor < 10 & prazo > 5') == \
        'Valor &lt; 10 &amp; prazo &gt; 5'


def test_plain_preserva_quebras_de_linha():
    # get_field_display converte \n em <br/> depois de sanitizar
    assert sanitize_html('linha1\nlinha2') == 'linha1\nlinha2'


def test_valores_vazios_atravessam():
    assert sanitize_html('') == ''
    assert sanitize_html(None) is None
    assert sanitize_html('', rich=True) == ''


@pytest.mark.parametrize('valor', [
    '<script>alert(1)</script>Ciente',
    'Valor < 10 & prazo > 5',
    'Encaminhado <b>ao</b> <a href="https://x">setor</a>',
    'texto &amp; cia',
])
def test_plain_e_idempotente(valor):
    """Propriedade da qual dependem as duas camadas (pre_save + renderização).

    Se sanitizar duas vezes não fosse estável, o valor gravado seria
    re-escapado a cada exibição.
    """
    uma_vez = sanitize_html(valor)
    assert sanitize_html(uma_vez) == uma_vez


@pytest.mark.parametrize('valor', [
    '<a href="https://camara.gov.br" target="_blank">Portal</a>',
    '<p style="text-align: center;">centro</p>',
    '<table><tr><td colspan="2">c</td></tr></table>',
    '<script>alert(1)</script><b>ok</b>',
])
def test_rich_e_idempotente(valor):
    uma_vez = sanitize_html(valor, rich=True)
    assert sanitize_html(uma_vez, rich=True) == uma_vez


def test_rich_preserva_links():
    saida = sanitize_html(
        '<a href="https://camara.gov.br" target="_blank">Portal</a>',
        rich=True)
    assert 'href="https://camara.gov.br"' in saida
    assert 'target="_blank"' in saida
    assert 'rel="noopener noreferrer"' in saida
    assert '>Portal</a>' in saida

    assert 'href="/materia/123"' in sanitize_html(
        '<a href="/materia/123">Matéria</a>', rich=True)
    assert 'href="mailto:a@b.c"' in sanitize_html(
        '<a href="mailto:a@b.c">mail</a>', rich=True)


def test_rich_remove_href_perigosa_mas_mantem_o_texto():
    saida = sanitize_html(
        '<a href="javascript:alert(1)">clique</a>', rich=True)
    assert 'javascript' not in saida
    assert 'clique' in saida


def test_rich_remove_script_e_manipuladores_de_evento():
    saida = sanitize_html('<script>alert(1)</script><b>ok</b>', rich=True)
    assert saida == '<b>ok</b>'

    assert 'onclick' not in sanitize_html(
        '<a href="#" onclick="steal()">x</a>', rich=True)
    assert 'onerror' not in sanitize_html(
        '<img src="x" onerror="alert(1)">', rich=True)


def test_rich_preserva_formatacao_do_tinymce():
    """Protege contra regressão visual no conteúdo já cadastrado."""
    assert 'style="text-align: center;"' in sanitize_html(
        '<p style="text-align: center;">centro</p>', rich=True)

    saida = sanitize_html(
        '<table><tr><td colspan="2">c</td></tr></table>', rich=True)
    assert '<table>' in saida and 'colspan="2"' in saida

    assert sanitize_html('<ul><li>a</li><li>b</li></ul>', rich=True) == \
        '<ul><li>a</li><li>b</li></ul>'


def test_sanitize_scope():
    assert sanitize_scope(TramitacaoAdministrativo, 'texto') == 'plain'
    assert sanitize_scope(ExpedienteSessao, 'conteudo') == 'rich'
    assert sanitize_scope(LexmlProvedor, 'xml') == 'exempt'


def test_sanitize_field_respeita_isencao():
    xml = '<xml><a href="javascript:x">y</a></xml>'
    assert sanitize_field(LexmlProvedor, 'xml', xml) == xml


@pytest.mark.django_db
def test_pre_save_sanitiza_campo_simples():
    t = baker.make(TramitacaoAdministrativo,
                   texto='<script>alert(1)</script>Ciente <b>ok</b>')
    t.refresh_from_db()
    assert t.texto == 'Ciente ok'


@pytest.mark.django_db
def test_pre_save_sanitiza_campo_rico_preservando_html():
    e = baker.make(ExpedienteSessao,
                   conteudo='<b>x</b><script>alert(1)</script>'
                            '<a href="https://a.b" target="_blank">l</a>')
    e.refresh_from_db()
    assert '<script>' not in e.conteudo
    assert '<b>x</b>' in e.conteudo
    assert 'href="https://a.b"' in e.conteudo


@pytest.mark.django_db
def test_pre_save_nao_toca_modelo_isento():
    xml = '<xml>a &amp; b <script>x</script></xml>'
    p = baker.make(LexmlProvedor, xml=xml)
    p.refresh_from_db()
    assert p.xml == xml


@pytest.mark.django_db
def test_get_field_display_nao_devolve_script():
    t = TramitacaoAdministrativo(texto='<script>alert(1)</script>Ciente')
    __, display = get_field_display(t, 'texto')
    assert '<script>' not in display
    assert 'Ciente' in display


@pytest.mark.django_db
def test_get_field_display_protege_linha_legada():
    """Linhas gravadas antes do pre_save não passam pela camada de entrada."""
    t = baker.make(TramitacaoAdministrativo, texto='ok')
    TramitacaoAdministrativo.objects.filter(pk=t.pk).update(
        texto='<script>alert(1)</script>legado')
    t.refresh_from_db()
    assert t.texto == '<script>alert(1)</script>legado'

    __, display = get_field_display(t, 'texto')
    assert '<script>' not in display
