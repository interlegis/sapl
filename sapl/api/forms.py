from django.db.models import Q
from django.forms.fields import CharField, MultiValueField
from django.forms.widgets import MultiWidget, TextInput
from django_filters.filters import MethodFilter, ModelChoiceFilter
from rest_framework.compat import django_filters
from rest_framework.filters import FilterSet

from sapl.base.models import Autor, TipoAutor
from sapl.utils import generic_relations_for_model


class SaplGenericRelationSearchFilterSet(FilterSet):
    q = MethodFilter()

    def filter_q(self, queryset, value):

        query = value.split(' ')
        if query:
            q = Q()
            for qtext in query:
                if not qtext:
                    continue
                q_fs = Q(nome__icontains=qtext)

                order_by = []

                for gr in generic_relations_for_model(self._meta.model):
                    sgr = gr[1]
                    for item in sgr:
                        if item.related_model != self._meta.model:

                            continue
                        flag_order_by = True
                        for field in item.fields_search:
                            if flag_order_by:
                                flag_order_by = False
                                order_by.append('%s__%s' % (
                                    item.related_query_name(),
                                    field[0])
                                )
                            # if len(field) == 3 and field[2](qtext) is not
                            # None:
                            q_fs = q_fs | Q(**{'%s__%s%s' % (
                                item.related_query_name(),
                                field[0],
                                field[1]): qtext if len(field) == 2
                                else field[2](qtext)})

                q = q & q_fs

            if q:
                queryset = queryset.filter(q).order_by(*order_by)

        return queryset


class SearchForFieldWidget(MultiWidget):

    def decompress(self, value):
        if value is None:
            return [None, None]
        return value

    def __init__(self, attrs=None):
        widgets = (TextInput, TextInput)
        MultiWidget.__init__(self, widgets, attrs)


class SearchForFieldField(MultiValueField):
    widget = SearchForFieldWidget

    def __init__(self, *args, **kwargs):
        fields = (
            CharField(),
            CharField())
        super(SearchForFieldField, self).__init__(fields, *args, **kwargs)

    def compress(self, parameters):
        if parameters:
            return parameters
        return None


class SearchForFieldFilter(django_filters.filters.MethodFilter):
    field_class = SearchForFieldField


class AutorChoiceFilterSet(SaplGenericRelationSearchFilterSet):
    q = MethodFilter()
    tipo = ModelChoiceFilter(queryset=TipoAutor.objects.all())

    class Meta:
        model = Autor
        fields = ['q',
                  'tipo',
                  'nome', ]

    def filter_q(self, queryset, value):
        return SaplGenericRelationSearchFilterSet.filter_q(
            self, queryset, value).distinct('nome').order_by('nome')


class AutorSearchForFieldFilterSet(AutorChoiceFilterSet):
    q = SearchForFieldFilter()

    class Meta(AutorChoiceFilterSet.Meta):
        pass

    def filter_q(self, queryset, value):

        value[0] = value[0].split(',')
        value[1] = value[1].split(',')

        params = {}
        for key, v in list(zip(value[0], value[1])):
            if v in ['True', 'False']:
                v = '1' if v == 'True' else '0'
            params[key] = v
        return queryset.filter(**params).distinct('nome').order_by('nome')
