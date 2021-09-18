
from sapl.api.core.filters import SaplFilterSetMixin
from sapl.sessao.models import SessaoPlenaria

# esta classe não é necessária
# a api construiría uma igual
# mas está demonstrar que caso queira customizar um filter_set
# que a api consiga recuperá-lo, para os endpoints básicos
# deve seguir os critérios de nomenclatura e herança

#  class [Model]FilterSet(SaplFilterSetMixin):
#      class Meta(SaplFilterSetMixin.Meta):


class SessaoPlenariaFilterSet(SaplFilterSetMixin):

    class Meta(SaplFilterSetMixin.Meta):
        model = SessaoPlenaria
