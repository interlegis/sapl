from django.db.models.fields.files import FileField
from django.template.defaultfilters import capfirst
import django_filters
from django_filters.filters import CharFilter, NumberFilter
from django_filters.rest_framework.filterset import FilterSet
from django_filters.utils import resolve_field
from sapl.sessao.models import SessaoPlenaria


class SaplFilterSetMixin(FilterSet):

    o = CharFilter(method='filter_o')

    class Meta:
        fields = '__all__'
        filter_overrides = {
            FileField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }

    def filter_o(self, queryset, name, value):
        try:
            return queryset.order_by(
                *map(str.strip, value.split(',')))
        except:
            return queryset

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr='exact'):
        # Redefine método estático para ignorar filtro para
        # fields que não possuam lookup_expr informado
        f, lookup_type = resolve_field(f, lookup_expr)

        default = {
            'field_name': name,
            'label': capfirst(f.verbose_name),
            'lookup_expr': lookup_expr
        }

        filter_class, params = cls.filter_for_lookup(
            f, lookup_type)
        default.update(params)
        if filter_class is not None:
            return filter_class(**default)
        return None


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
