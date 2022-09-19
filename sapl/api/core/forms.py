
from sapl.api.core.filters import SaplFilterSetMixin
from sapl.sessao.models import SessaoPlenaria

# ATENÇÃO: MUDANÇAS NO CORE DEVEM SER REALIZADAS COM
#          EXTREMA CAUTELA E CONSCIENTE DOS IMPACTOS NA API

# FILTER SET dentro do core devem ser criados se o intuíto é um filter-set
# para o list da api.
# filter_set para actions, devem ser criados fora do core.

# A CLASSE SessaoPlenariaFilterSet não é necessária
# o construtor da api construiría uma igual
# mas está aqui para demonstrar que caso queira customizar um filter_set
# que a api consiga recuperá-lo, para os endpoints básicos
# deve seguir os critérios de nomenclatura e herança

#  class [Model]FilterSet(SaplFilterSetMixin):
#      class Meta(SaplFilterSetMixin.Meta):


class SessaoPlenariaFilterSet(SaplFilterSetMixin):

    class Meta(SaplFilterSetMixin.Meta):
        model = SessaoPlenaria
