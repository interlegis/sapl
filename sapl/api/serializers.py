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
        fields = ['id', 'nome']


class AutorObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        return str(value)


class AutorSerializer(serializers.ModelSerializer):
    autor_related = AutorObjectRelatedField(read_only=True)

    class Meta:
        model = Autor
        fields = ['id', 'tipo', 'nome', 'object_id', 'autor_related', 'user']
