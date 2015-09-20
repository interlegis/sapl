from django import template
from django.core.signing import Signer
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
    return value[key]


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
def close_div(value_max, value_min):
    return '</div>' * (int(value_max) - int(value_min) + 1)


@register.filter
def get_sign_vigencia(value):
    string = "%s,%s" % (value.inicio_vigencia, value.fim_vigencia)
    signer = Signer()
    return signer.sign(str(string))
