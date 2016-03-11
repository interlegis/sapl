from django import template
from django.core.signing import Signer
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from compilacao.models import Dispositivo, TipoDispositivo

register = template.Library()


@register.filter
def get_bloco_atualizador(pk_atualizador):
    return Dispositivo.objects.order_by('ordem_bloco_atualizador').filter(
        Q(dispositivo_pai_id=pk_atualizador) |
        Q(dispositivo_atualizador_id=pk_atualizador)).select_related()


@register.filter
def get_tipos_dispositivo(pk_atual):

    return TipoDispositivo.objects.filter(
        id__gte=pk_atual)


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
    if dispositivo.ta_publicado is not None:
        d = dispositivo.dispositivo_atualizador.dispositivo_pai
        if dispositivo.texto == Dispositivo.TEXTO_PADRAO_DISPOSITIVO_REVOGADO:
            return _('Revogado pelo %s - %s.') % (
                d, ta_pub_list[dispositivo.ta_publicado_id])
        elif not dispositivo.dispositivo_substituido_id:
            return _('Inclusão feita pelo %s - %s.') % (
                d, ta_pub_list[dispositivo.ta_publicado_id])
        else:
            return _('Alteração feita pelo %s - %s.') % (
                d, ta_pub_list[dispositivo.ta_publicado_id])
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
def is_relative_auto_insert(dpt, request):
    return dpt.is_relative_auto_insert(request.session['perfil_estrutural'])


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

    # conteudo e menu no filho
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
        result = '(' + d.tipo_dispositivo.nome + ' ' + \
            d.rotulo_padrao() + ')'
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
    return '%s:detail' % obj.content_type.model
