from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import DateFilter, MethodFilter, ModelChoiceFilter
from rest_framework import serializers
from rest_framework.filters import FilterSet

from sapl.api.forms import SaplGenericRelationSearchFilterSet,\
    SearchForFieldFilter
from sapl.base.models import Autor, TipoAutor
from sapl.parlamentares.models import Legislatura


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


class AutoresPossiveisFilterSet(FilterSet):
    data_relativa = DateFilter(method='filter_data_relativa')
    tipo = MethodFilter(required=True)

    class Meta:
        model = Autor
        fields = ['data_relativa', 'tipo', ]

    def filter_data_relativa(self, queryset, name, value):
        return queryset

    def filter_tipo(self, queryset, value):
        try:
            tipo = TipoAutor.objects.get(pk=value)
        except:
            raise serializers.ValidationError(_('Tipo de Autor inexistente.'))

        qs = queryset.filter(tipo=tipo)

        return qs

    @property
    def qs(self):
        qs = super().qs

        data_relativa = self.form.cleaned_data['data_relativa'] \
            if 'data_relativa' in self.form.cleaned_data else None

        tipo = self.form.cleaned_data['tipo'] \
            if 'tipo' in self.form.cleaned_data else None

        if not tipo:
            return qs
        else:
            tipo = TipoAutor.objects.get(pk=tipo)
            if not tipo.content_type:
                return qs

        filter_for_model = 'filter_%s' % tipo.content_type.model

        if not hasattr(self, filter_for_model):
            return qs

        if not data_relativa:
            data_relativa = timezone.now()

        return getattr(self, filter_for_model)(qs, data_relativa).distinct()

    def filter_parlamentar(self, queryset, data_relativa):
        # não leva em conta afastamentos
        legislatura_relativa = Legislatura.objects.filter(
            data_inicio__lte=data_relativa,
            data_fim__gte=data_relativa).first()

        q = Q(
            parlamentar_set__mandato__data_inicio_mandato__lte=data_relativa,
            parlamentar_set__mandato__data_fim_mandato__isnull=True) | Q(
            parlamentar_set__mandato__data_inicio_mandato__lte=data_relativa,
            parlamentar_set__mandato__data_fim_mandato__gte=data_relativa)

        if legislatura_relativa.atual():
            q = q & Q(parlamentar_set__ativo=True)

        return queryset.filter(q)

    def filter_comissao(self, queryset, data_relativa):
        return queryset.filter(
            Q(comissao_set__data_extincao__isnull=True,
              comissao_set__data_fim_comissao__isnull=True) |
            Q(comissao_set__data_extincao__gte=data_relativa,
              comissao_set__data_fim_comissao__isnull=True) |
            Q(comissao_set__data_extincao__gte=data_relativa,
              comissao_set__data_fim_comissao__isnull=True) |
            Q(comissao_set__data_extincao__isnull=True,
              comissao_set__data_fim_comissao__gte=data_relativa) |
            Q(comissao_set__data_extincao__gte=data_relativa,
              comissao_set__data_fim_comissao__gte=data_relativa),
            comissao_set__data_criacao__lte=data_relativa)

    def filter_frente(self, queryset, data_relativa):
        return queryset.filter(
            Q(frente_set__data_extincao__isnull=True) |
            Q(frente_set__data_extincao__gte=data_relativa),
            frente_set__data_criacao__lte=data_relativa)

    def filter_bancada(self, queryset, data_relativa):
        return queryset.filter(
            Q(bancada_set__data_extincao__isnull=True) |
            Q(bancada_set__data_extincao__gte=data_relativa),
            bancada_set__data_criacao__lte=data_relativa)

    def filter_bloco(self, queryset, data_relativa):
        return queryset.filter(
            Q(bloco_set__data_extincao__isnull=True) |
            Q(bloco_set__data_extincao__gte=data_relativa),
            bloco_set__data_criacao__lte=data_relativa)

    def filter_orgao(self, queryset, data_relativa):
        # na implementação, não havia regras a implementar para orgao
        return queryset
