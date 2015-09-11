from django import template
from django.db.models import Q

from compilacao.models import Dispositivo

register = template.Library()


@register.filter
def get_bloco(pk):
    return Dispositivo.objects.order_by('ordem_bloco_atualizador').filter(
        Q(dispositivo_pai_id=pk) |
        Q(dispositivo_atualizador=pk)).select_related()
