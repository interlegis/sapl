from rest_framework import serializers
from sapl.base.models import Autor
from sapl.materia.models import MateriaLegislativa


class ChoiceSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return obj[1]

    def get_value(self, obj):
        return obj[0]


class ModelChoiceSerializer(ChoiceSerializer):

    def get_text(self, obj):
        return str(obj)

    def get_value(self, obj):
        return obj.id


class ModelChoiceObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        return ModelChoiceSerializer(value).data


class AutorChoiceSerializer(ModelChoiceSerializer):

    def get_text(self, obj):
        return obj.nome

    class Meta:
        model = Autor
        fields = ['id', 'nome']


class AutorSerializer(serializers.ModelSerializer):
    autor_related = ModelChoiceObjectRelatedField(read_only=True)

    class Meta:
        model = Autor


class MateriaLegislativaSerializer(serializers.ModelSerializer):

    class Meta:
        model = MateriaLegislativa
