
from sapl.api.core.filters import SaplFilterSetMixin
from sapl.sessao.models import SessaoPlenaria


class SessaoPlenariaFilterSet(SaplFilterSetMixin):
    class Meta(SaplFilterSetMixin.Meta):
        model = SessaoPlenaria
