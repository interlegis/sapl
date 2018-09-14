from rest_framework import serializers

from sapl.api.serializers import ModelChoiceSerializer,\
    ModelChoiceObjectRelatedField
from sapl.base.models import Autor


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
        fields = '__all__'
