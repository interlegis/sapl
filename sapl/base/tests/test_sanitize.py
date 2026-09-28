import pytest
from django.db.models.signals import pre_save
from django.template import Context, Template
from model_bakery import baker

from sapl.compilacao.forms import TipoDispositivoForm
from sapl.compilacao.models import TipoDispositivo, TipoTextoArticulado
from sapl.crispy_layout_mixin import get_field_display
from sapl.lexml.models import LexmlProvedor
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import TramitacaoAdministrativo
from sapl.sanitize import (html_fragment_is_balanced, sanitize_field,
                           sanitize_html, sanitize_scope)
from sapl.sessao.models import ExpedienteSessao


def test_plain_remove_marcacao_e_preserva_texto():
    assert sanitize_html('<script>alert(1)</script>Ciente') == 'Ciente'
    assert sanitize_html('Encaminhado <b>ao</b> setor') == \
        'Encaminhado ao setor'
    assert sanitize_html('<img src=x onerror=alert(1)>') == ''
    assert sanitize_html('<div>a</div><div>b</div>') == 'ab'


def test_plain_guarda_texto_puro_sem_escape():
    """O escape é da renderização; gravado escapado, apareceria &amp; na tela."""
    assert sanitize_html('Valor < 10 & prazo > 5') == 'Valor < 10 & prazo > 5'
    assert sanitize_html('ALFA &amp; BETA') == 'ALFA & BETA'


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
    """Salvar de novo um registro já sanitizado não altera o texto."""
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
    assert sanitize_scope(TipoTextoArticulado, 'rodape_global') == 'exempt'
    assert sanitize_scope(Parlamentar, 'biografia') == 'rich'


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


def test_pre_save_ignora_raw():
    """loaddata (inclusive em migrations) grava o objeto literalmente."""
    t = TramitacaoAdministrativo(texto='<b>fixture</b>')
    pre_save.send(sender=TramitacaoAdministrativo, instance=t, raw=True)
    assert t.texto == '<b>fixture</b>'


def test_get_field_display_escapa_texto_puro_uma_unica_vez():
    t = TramitacaoAdministrativo(texto='ALFA & BETA < 30')
    __, display = get_field_display(t, 'texto')
    assert 'ALFA &amp; BETA &lt; 30' in display
    assert '&amp;amp;' not in display


def test_get_field_display_escapa_campo_isento():
    p = LexmlProvedor(xml='<xml><script>x</script></xml>')
    __, display = get_field_display(p, 'xml')
    assert '<script>' not in display
    assert '&lt;xml&gt;' in display


def test_striptags_apos_sanitize_nao_escapa_duas_vezes():
    """Blocos da ata: texto puro, sem entidades escapadas de novo."""
    t = Template('{% load common_tags %}{{ v|sanitize|striptags }}')
    saida = t.render(Context({
        'v': '<p>Ofício&nbsp;12 lido &amp; arquivado</p>'
             '<script>alert(1)</script><img src=x onerror=alert(1)>'}))
    assert saida == 'Ofício&nbsp;12 lido &amp; arquivado'


@pytest.mark.parametrize('valor, esperado', [
    ('<br>', True),
    ('<br/>', True),
    ('<div class="titulo">Justificativa</div>', True),
    ('Art. ', True),
    ('<span class="x">', False),
    ('</span>', False),
    ('<b><i>x</b></i>', False),
])
def test_html_fragment_is_balanced(valor, esperado):
    assert html_fragment_is_balanced(valor) is esperado


@pytest.mark.django_db
def test_tipo_dispositivo_form_rejeita_fragmento_desbalanceado():
    td = baker.make(TipoDispositivo)
    dados = {f: getattr(td, f) or '' for f in TipoDispositivoForm.Meta.fields}
    dados['rotulo_prefixo_html'] = '<span class="rotulo">'
    dados['rotulo_sufixo_html'] = '</span>'
    form = TipoDispositivoForm(data=dados, instance=td)
    assert not form.is_valid()
    assert 'rotulo_prefixo_html' in form.errors
    assert 'rotulo_sufixo_html' in form.errors

    dados['rotulo_prefixo_html'] = '<br/>'
    dados['rotulo_sufixo_html'] = ''
    form = TipoDispositivoForm(data=dados, instance=td)
    assert 'rotulo_prefixo_html' not in form.errors
