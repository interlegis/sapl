from django.db.models import Q
from django_filters.filters import MethodFilter, ModelChoiceFilter
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
                    model = gr[0]
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
                            q_fs = q_fs | Q(**{'%s__%s%s' % (
                                item.related_query_name(),
                                field[0],
                                field[1]): qtext})

                q = q & q_fs

            if q:
                queryset = queryset.filter(q).order_by(*order_by)

        return queryset


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
            self, queryset, value).order_by('nome')
