
from collections import OrderedDict

from django.db.models.fields.files import FileField
from django.template.defaultfilters import capfirst
from django_filters.constants import ALL_FIELDS
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from django_filters.utils import resolve_field, get_all_model_fields
import django_filters

# ATENÇÃO: MUDANÇAS NO CORE DEVEM SER REALIZADAS COM
#          EXTREMA CAUTELA E CONSCIENTE DOS IMPACTOS NA API


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
    def get_fields(cls):
        model = cls._meta.model
        fields_model = get_all_model_fields(model)
        fields_filter = cls._meta.fields
        exclude = cls._meta.exclude

        if exclude is not None and fields_filter is None:
            fields_filter = ALL_FIELDS

        fields = fields_filter if isinstance(fields_filter, dict) else {}

        for f_str in fields_model:
            if f_str not in fields:

                f = model._meta.get_field(f_str)

                if f.many_to_many:
                    fields[f_str] = ['exact']
                    continue

                fields[f_str] = ['exact']

                def get_keys_lookups(cl, sub_f):
                    r = []
                    for lk, lv in cl.items():

                        if lk == 'contained_by':
                            continue

                        sflk = f'{sub_f}{"__" if sub_f else ""}{lk}'
                        r.append(sflk)

                        if hasattr(lv, 'class_lookups'):
                            r += get_keys_lookups(lv.class_lookups, sflk)

                        if hasattr(lv, 'output_field') and hasattr(lv, 'output_field.class_lookups'):
                            r.append(f'{sflk}{"__" if sflk else ""}range')

                            r += get_keys_lookups(lv.output_field.class_lookups, sflk)

                    return r

                fields[f_str] = list(
                    set(fields[f_str] + get_keys_lookups(f.class_lookups, '')))

        # Remove excluded fields
        exclude = exclude or []

        fields = [(f, lookups)
                  for f, lookups in fields.items() if f not in exclude]

        return OrderedDict(fields)

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
