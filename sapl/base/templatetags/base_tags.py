
from django import template

register = template.Library()


@register.filter
def tipoautor_contenttype_list(tipo):
    return 'sapl.' + tipo.content_type.app_label + ':' + tipo.content_type.model + '_list'
