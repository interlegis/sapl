
from django import template
from django.core.signing import Signer
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from sapl.compilacao.models import Dispositivo

register = template.Library()


class DispositivoTreeNode(template.Node):

    def __init__(self, template_nodes, dispositivo_list_var):
        self.template_nodes = template_nodes
        self.dispositivo_list_var = dispositivo_list_var

    def _render_node(self, context, node):
        bits_alts = []
        bits_filhos = []
        context.push()
        for child in node['alts']:
            bits_alts.append(self._render_node(context, child))
        for child in node['filhos']:
            bits_filhos.append(self._render_node(context, child))
        context['node'] = node
        context['alts'] = mark_safe(''.join(bits_alts))
        context['filhos'] = mark_safe(''.join(bits_filhos))
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered

    def render(self, context):
        dispositivo_list_var = self.dispositivo_list_var.resolve(context)
        bits = [self._render_node(context, node)
                for node in dispositivo_list_var]
        return ''.join(bits)


@register.tag
def dispositivotree(parser, token):

    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            _('%s tag requires a queryset') % bits[0])

    dispositivo_list_var = template.Variable(bits[1])

    template_nodes = parser.parse(('enddispositivotree',))
    parser.delete_first_token()

    return DispositivoTreeNode(template_nodes, dispositivo_list_var)

# --------------------------------------------------------------


@register.filter
def get_bloco_atualizador(pk_atualizador):
    return Dispositivo.objects.order_by('ordem_bloco_atualizador').filter(
        Q(dispositivo_pai_id=pk_atualizador) |
        Q(dispositivo_atualizador_id=pk_atualizador)).select_related()


@register.simple_tag
def dispositivo_desativado(dispositivo, inicio_vigencia, fim_vigencia):
    if inicio_vigencia and fim_vigencia:
        if dispositivo.fim_vigencia is None:
            return ''
        elif dispositivo.fim_vigencia >= fim_vigencia:
            return ''
        return 'desativado'
    else:
        if dispositivo.fim_vigencia is not None:
            return 'desativado'
    return ''


@register.simple_tag
def nota_automatica(dispositivo, ta_pub_list):

    if dispositivo.ta_publicado:
        d = dispositivo.dispositivo_atualizador.dispositivo_pai

        ta_publicado = ta_pub_list[dispositivo.ta_publicado_id] if\
            ta_pub_list else dispositivo.ta_publicado

        if dispositivo.dispositivo_de_revogacao:
            return _('Revogado pelo %s - %s.') % (
                d, ta_publicado)
        elif not dispositivo.dispositivo_substituido_id:
            return _('Inclusão feita pelo %s - %s.') % (
                d, ta_publicado)
        else:
            return _('Alteração feita pelo %s - %s.') % (
                d, ta_publicado)

    return ''


@register.simple_tag
def set_nivel_old(view, value):
    view.flag_nivel_old = value
    return ''


@register.simple_tag
def close_div(value_max, value_min, varr):
    return mark_safe('</div>' * (int(value_max) - int(value_min) + 1 + varr))


@register.filter
def get_sign_vigencia(value):
    string = "%s,%s,%s" % (
        value.ta_publicado_id if value.ta_publicado_id else 0,
        value.inicio_vigencia,
        value.fim_vigencia)
    signer = Signer()
    return signer.sign(str(string))


@register.filter
def select_provaveis_inserts(view, request):
    return view.select_provaveis_inserts(request)


@register.filter
def isinst(value, class_str):
    classe = value.__class__.__name__
    return classe == class_str


@register.filter
def render_actions_head(view, d_atual):

    if view.__class__.__name__ != 'DispositivoSimpleEditView':
        return False

    # Menu
    if view.pk_view == view.pk_edit and d_atual.pk == view.pk_view:
        return True

    # conteudo e menu no filho - ocorre nas inclusões feitas através do editor
    if view.pk_view != view.pk_edit and d_atual.pk == view.pk_edit:
        return True

    return False


@register.filter
def short_string(str, length):
    if len(str) > length:
        return str[:length] + '...'
    else:
        return str


@register.filter
def nomenclatura(d):
    result = ''
    if d.rotulo != '':
        if d.tipo_dispositivo.rotulo_prefixo_texto != '':
            result = d.rotulo
        else:
            result = '(' + d.tipo_dispositivo.nome + ' ' + \
                d.rotulo + ')'
    else:
        r = d.rotulo_padrao()
        if r:
            r += ' '
        result = '(' + d.tipo_dispositivo.nome + r + ')'
    return result


def update_dispositivos_parents(dpts_parents, ta_id):

    dpts = Dispositivo.objects.order_by('ordem').filter(
        ta_id=ta_id).values_list(
        'pk', 'dispositivo_pai_id', 'rotulo', 'tipo_dispositivo__nome',
        'tipo_dispositivo__rotulo_prefixo_texto')

    for d in dpts:
        dpts_parents[str(d[0])] = {
            'd': d, 'p': [], 'h': None}

    def parents(k):
        pai = dpts_parents[str(k)]['d'][1]
        p = dpts_parents[str(k)]['p']
        if not p:
            if pai:
                parent_k = [pai, ] + parents(pai)
            else:
                parent_k = []
        else:
            parent_k = p

        return parent_k

    for k in dpts_parents:
        dpts_parents[str(k)]['p'] = parents(k)


@register.simple_tag
def heranca(request, d, ignore_ultimo=0, ignore_primeiro=0):
    ta_dpts_parents = request.session.get('herancas')

    if not ta_dpts_parents:
        ta_dpts_parents = {}

    ta_id = str(d.ta_id)
    d_pk = str(d.pk)
    if ta_id not in ta_dpts_parents or d_pk not in ta_dpts_parents[ta_id]:
        # print('recarregando estrutura temporaria de heranças')
        dpts_parents = {}
        ta_dpts_parents[ta_id] = dpts_parents
        update_dispositivos_parents(dpts_parents, ta_id)

        herancas_fila = request.session.get('herancas_fila')
        if not herancas_fila:
            herancas_fila = []

        herancas_fila.append(ta_id)
        if len(herancas_fila) > 100:
            ta_remove = herancas_fila.pop(0)
            del ta_dpts_parents[str(ta_remove)]

        request.session['herancas_fila'] = herancas_fila
        request.session['herancas'] = ta_dpts_parents

    h = ta_dpts_parents[ta_id][d_pk]['h']

    if h:
        return h

    dpts_parents = ta_dpts_parents[ta_id]
    parents = dpts_parents[d_pk]['p']
    result = ''

    if parents:
        pk_last = parents[-1]
    for pk in parents:

        if ignore_ultimo and pk == pk_last:
            break

        if ignore_primeiro:
            ignore_primeiro = 0
            continue

        p = dpts_parents[str(pk)]['d']

        if p[4] != '':
            result = p[2] + ' ' + result
        else:
            result = '(' + p[3] + ' ' + \
                p[2] + ')' + ' ' + result

    dpts_parents[d_pk]['h'] = result
    return result


@register.simple_tag
def nomenclatura_heranca(d, ignore_ultimo=0, ignore_primeiro=0):
    result = ''
    while d is not None:

        if ignore_ultimo and d.dispositivo_pai is None:
            break
        if ignore_primeiro:
            ignore_primeiro = 0
            d = d.dispositivo_pai
            continue

        if d.rotulo != '':
            if d.tipo_dispositivo.rotulo_prefixo_texto != '':
                result = d.rotulo + ' ' + result
            else:
                result = '(' + d.tipo_dispositivo.nome + ' ' + \
                    d.rotulo + ')' + ' ' + result
        else:
            result = '(' + d.tipo_dispositivo.nome + \
                d.rotulo_padrao() + ')' + ' ' + result
        d = d.dispositivo_pai

    return result


@register.filter
def urldetail_content_type(obj):
    return '%s:%s_detail' % (
        obj.content_object._meta.app_config.name, obj.content_type.model)


@register.filter
def list(obj):
    return [obj, ]


@register.filter
def can_use_dynamic_editing(texto_articulado, user):
    return texto_articulado.can_use_dynamic_editing(user)
