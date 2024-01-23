import logging

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import CharFilter, DateFilter, ModelChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework import serializers

from drfautoapi.drfautoapi import ApiFilterSetMixin
from sapl.base.models import TipoAutor, Autor
from sapl.parlamentares.models import Legislatura
from sapl.utils import generic_relations_for_model

logger = logging.getLogger(__name__)


class SaplFilterSetMixin(ApiFilterSetMixin):
    pass


class AutorFilterSet(SaplFilterSetMixin):
    q = CharFilter(method='filter_q')
    tipo = ModelChoiceFilter(queryset=TipoAutor.objects.all())

    def filter_q(self, queryset, name, value):

        query = value.split(' ')
        if query:
            q = Q()
            for qtext in query:
                if not qtext:
                    continue
                q_fs = Q(nome__icontains=qtext) | Q(
                    tipo__descricao__icontains=qtext)

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

        return queryset.distinct()


class AutoresPossiveisFilterSet(SaplFilterSetMixin):
    data_relativa = DateFilter(method='filter_data_relativa')
    tipo = CharFilter(method='filter_tipo')

    class Meta:
        model = Autor
        fields = ['data_relativa', 'tipo', ]

    def filter_data_relativa(self, queryset, name, value):
        return queryset

    def filter_tipo(self, queryset, name, value):

        try:
            logger.debug(
                "Tentando obter TipoAutor correspondente à pk {}.".format(value))
            tipo = TipoAutor.objects.get(pk=value)
        except:
            logger.error("TipoAutor(pk={}) inexistente.".format(value))
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

        # Se cadastro em Janeiro e início da legislatura/mandato em Fevereiro
        if not legislatura_relativa:
            # ordering de Legislatura é DESC por padrão, então pega a última legislatura
            legislatura_relativa = Legislatura.objects.filter(
                data_inicio__year=data_relativa.year
            ).first()
            data_relativa = legislatura_relativa.data_inicio

        q = Q(
            parlamentar_set__mandato__data_inicio_mandato__lte=data_relativa,
            parlamentar_set__mandato__data_fim_mandato__isnull=True) | Q(
            parlamentar_set__mandato__data_inicio_mandato__lte=data_relativa,
            parlamentar_set__mandato__data_fim_mandato__gte=data_relativa)

        if legislatura_relativa.atual():
            q = q & Q(parlamentar_set__ativo=True)

        legislatura_anterior = self.request.GET.get(
            'legislatura_anterior', 'False')
        if legislatura_anterior.lower() == 'true':
            legislaturas = Legislatura.objects.filter(
                data_fim__lte=data_relativa).order_by('-data_fim')[:2]
            if len(legislaturas) == 2:
                _, leg_anterior = legislaturas
                q = q | Q(
                    parlamentar_set__mandato__data_inicio_mandato__gte=leg_anterior.data_inicio)

        qs = queryset.filter(q)
        return qs

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
