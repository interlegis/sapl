"""Sanitização de HTML/JavaScript nos campos de texto livre do SAPL.

Módulo sem dependências internas do SAPL de propósito: é importado por
``sapl.crispy_layout_mixin``, ``sapl.base.receivers`` e pelos templatetags,
e ``sapl.utils`` já importa ``sapl.crispy_layout_mixin``.

Duas políticas:

* ``plain`` — remove toda a marcação e guarda texto puro, com as entidades
  já decodificadas: o escape fica por conta da renderização. É o padrão para
  qualquer ``TextField``.
* ``rich`` — allowlist para os campos editados via TinyMCE, que contêm HTML
  legítimo (negrito, listas, tabelas e links).

A ``rich`` é idempotente, o que permite aplicá-la tanto no ``pre_save`` quanto
na renderização. A ``plain`` só não é idempotente para texto que seja HTML
codificado em entidades (``&lt;b&gt;``): a primeira passada decodifica, a
segunda remove a tag. Na renderização, campos ``plain`` são escapados em vez
de re-sanitizados.
"""

import html
from html.parser import HTMLParser

import nh3

SANITIZE_RICH_TAGS = {
    'p', 'br', 'hr', 'div', 'span',
    'b', 'strong', 'i', 'em', 'u', 's', 'strike', 'sub', 'sup',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd', 'blockquote', 'pre', 'code',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
    'col', 'colgroup',
    'a', 'img',
}

# 'style' mantém o alinhamento produzido pelos botões do TinyMCE;
# 'target' mantém o "abrir em nova aba" dos links já cadastrados.
# 'rel' não pode entrar aqui: o nh3 aborta se a tag 'a' declarar 'rel'
# ao mesmo tempo em que link_rel está definido — ele mesmo escreve o atributo.
SANITIZE_RICH_ATTRS = {
    '*': {'style', 'class', 'align', 'title', 'dir', 'lang'},
    'a': {'href', 'target', 'name'},
    'img': {'src', 'alt', 'width', 'height'},
    'td': {'colspan', 'rowspan', 'headers'},
    'th': {'colspan', 'rowspan', 'scope', 'headers'},
    'col': {'span'},
    'colgroup': {'span'},
    'table': {'border', 'cellpadding', 'cellspacing', 'summary'},
}

SANITIZE_URL_SCHEMES = {'http', 'https', 'mailto', 'tel'}

# O conteúdo destas tags é descartado junto com a tag. Sem isso o texto de
# dentro de um <script> sobreviveria como texto solto.
SANITIZE_CLEAN_CONTENT_TAGS = {'script', 'style'}

# Campos que guardam HTML legítimo, indexados por '<app_label>.<Model>'.
# Os de sessao e compilacao.Dispositivo são editados no TinyMCE; os de
# compilacao.TipoDispositivo são fragmentos de template configurados por
# administradores.
RICH_TEXT_FIELDS = {
    'base.CasaLegislativa': {'informacao_geral'},
    'norma.NormaRelacionada': {'resumo'},
    'parlamentares.Legislatura': {'observacao'},
    'parlamentares.Parlamentar': {'biografia'},
    'sessao.ExpedienteSessao': {'conteudo'},
    'sessao.OcorrenciaSessao': {'conteudo'},
    'sessao.ConsideracoesFinais': {'conteudo'},
    'compilacao.Dispositivo': {'texto', 'texto_atualizador'},
    'compilacao.TipoDispositivo': {
        'rotulo_prefixo_html', 'rotulo_sufixo_html',
        'texto_prefixo_html', 'texto_sufixo_html',
        'nota_automatica_prefixo_html', 'nota_automatica_sufixo_html',
    },
}

# Campos que não devem ser tocados em hipótese alguma.
SANITIZE_EXEMPT_FIELDS = {
    # xml é XML fornecido pela equipe do LexML; já é escapado em pretty_xml
    'lexml.LexmlProvedor': {'xml'},
    # rodape_global é interpolado dentro de um content: de CSS
    'compilacao.TipoTextoArticulado': {'rodape_global'},
}


def model_key(model):
    return '{}.{}'.format(model._meta.app_label, model.__name__)


def sanitize_scope(model, fieldname):
    """Retorna 'exempt', 'rich' ou 'plain' para um campo de um modelo."""
    key = model_key(model)
    if fieldname in SANITIZE_EXEMPT_FIELDS.get(key, ()):
        return 'exempt'
    if fieldname in RICH_TEXT_FIELDS.get(key, ()):
        return 'rich'
    return 'plain'


def sanitize_html(value, rich=False):
    """Remove HTML/JavaScript perigoso de ``value``.

    Com ``rich=False`` toda a marcação é removida e apenas o texto sobra,
    sem escape: ``&`` continua ``&``.
    Com ``rich=True`` aplica-se a allowlist: links são preservados, mas
    esquemas de URL fora de SANITIZE_URL_SCHEMES (javascript:, data:) e
    manipuladores de evento (onclick, onerror) são descartados.
    """
    if not value:
        return value

    if not isinstance(value, str):
        value = str(value)

    if rich:
        return nh3.clean(
            value,
            tags=SANITIZE_RICH_TAGS,
            attributes=SANITIZE_RICH_ATTRS,
            url_schemes=SANITIZE_URL_SCHEMES,
            clean_content_tags=SANITIZE_CLEAN_CONTENT_TAGS,
            link_rel='noopener noreferrer',
            strip_comments=True)

    return html.unescape(nh3.clean(
        value,
        tags=set(),
        attributes={},
        clean_content_tags=SANITIZE_CLEAN_CONTENT_TAGS,
        link_rel=None,
        strip_comments=True))


def sanitize_field(model, fieldname, value):
    """Sanitiza ``value`` conforme a política do campo.

    Campos isentos atravessam sem modificação.
    """
    scope = sanitize_scope(model, fieldname)
    if scope == 'exempt':
        return value
    return sanitize_html(value, rich=(scope == 'rich'))


_VOID_TAGS = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
    'meta', 'param', 'source', 'track', 'wbr',
}


class _BalanceChecker(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.balanced = True

    def handle_starttag(self, tag, attrs):
        if tag not in _VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in _VOID_TAGS:
            return
        if not self.stack or self.stack.pop() != tag:
            self.balanced = False


def html_fragment_is_balanced(value):
    """Indica se toda tag aberta em ``value`` é fechada nele mesmo.

    Fragmentos desbalanceados (``<span>`` num campo, ``</span>`` em outro)
    são reescritos pela sanitização ``rich``, que fecha ou descarta as tags.
    """
    checker = _BalanceChecker()
    checker.feed(value)
    checker.close()
    return checker.balanced and not checker.stack
