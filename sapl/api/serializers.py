from django.contrib.contenttypes.fields import GenericRel
from rest_framework import serializers

from sapl.base.models import Autor
from sapl.utils import SaplGenericRelation


class ChoiceSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return obj[1]

    def get_value(self, obj):
        return obj[0]


class AutorChoiceSerializer(ChoiceSerializer):

    def get_text(self, obj):
        return obj.nome

    def get_value(self, obj):
        return obj.id

    class Meta:
        model = Autor
        fields = ['id', 'tipo', 'nome', 'object_id', 'autor_related', 'user']

# Models que apontaram uma GenericRelation com Autor


def autores_models_generic_relations():
    models_of_generic_relations = list(map(
        lambda x: x.related_model,
        filter(
            lambda obj: obj.is_relation and
            hasattr(obj, 'field') and
            isinstance(obj, GenericRel),

            Autor._meta.get_fields(include_hidden=True))
    ))

    models = list(map(
        lambda x: (x,
                   list(filter(
                       lambda field: (
                           isinstance(
                               field, SaplGenericRelation) and
                           field.related_model == Autor),
                       x._meta.get_fields(include_hidden=True)))),
        models_of_generic_relations
    ))

    return models


class AutorObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):

        return str(value)

        for gr in autores_models_generic_relations():
            if isinstance(value, gr[0]):
                verbose_name = gr[0]._meta.verbose_name
                fields_search = gr[1][0].fields_search

        raise Exception(_('Erro na seleção de autor'))


class AutorSerializer(serializers.ModelSerializer):

    autor_related = AutorObjectRelatedField(read_only=True)

    class Meta:
        model = Autor
        fields = ['id', 'tipo', 'nome', 'object_id', 'autor_related', 'user']
