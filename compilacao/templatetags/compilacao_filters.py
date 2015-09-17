from builtins import ValueError

from django import template
from django.db.models import Q

from compilacao.models import Dispositivo


register = template.Library()


@register.filter
def get_bloco(pk_atualizador):
    return Dispositivo.objects.order_by('ordem_bloco_atualizador').filter(
        Q(dispositivo_pai_id=pk_atualizador) |
        Q(dispositivo_atualizador_id=pk_atualizador)).select_related()


@register.filter
def get_field(value, key):
    try:
        return value[key]
    except ValueError:
        return None


@register.filter
def bloco_ja_incluso(view, bloco):
    try:
        return view.itens_de_bloco.index(bloco) >= 0
    except ValueError:
        return False


@register.simple_tag
def dispositivo_desativado(dispositivo):
    if dispositivo.fim_vigencia is not None:
        return 'desativado'
    return ''


@register.simple_tag
def nota_automatica(dispositivo):
    # return ''
    if dispositivo.norma_publicada is not None and \
            dispositivo.tipo_dispositivo.class_css != 'artigo':
        d = dispositivo.dispositivo_atualizador.dispositivo_pai
        return 'Alteração feita pelo %s.' % d
    return ''


@register.simple_tag
def set_nivel_old(view, value):
    view.flag_nivel_old = value
    return ''


@register.simple_tag
def append_to_itens_de_bloco(view, value):
    view.itens_de_bloco.append(value)
    return ''


@register.simple_tag
def close_div(value_max, value_min):
    return '</div>' * (int(value_max) - int(value_min) + 1)
