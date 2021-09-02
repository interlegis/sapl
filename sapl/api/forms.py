

from django_filters.filters import NumberFilter

from sapl.api.core.filters import SaplFilterSetMixin
from sapl.sessao.models import SessaoPlenaria


class SessaoPlenariaFilterSet(SaplFilterSetMixin):
    year = NumberFilter(method='filter_year')
    month = NumberFilter(method='filter_month')

    class Meta(SaplFilterSetMixin.Meta):
        model = SessaoPlenaria

    def filter_year(self, queryset, name, value):
        qs = queryset.filter(data_inicio__year=value)
        return qs

    def filter_month(self, queryset, name, value):
        qs = queryset.filter(data_inicio__month=value)
        return qs
