from rest_framework import serializers

from sapl.base.models import Autor
from sapl.materia.models import MateriaLegislativa
from sapl.sessao.models import SessaoPlenaria


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
        fields = '__all__'


class MateriaLegislativaSerializer(serializers.ModelSerializer):

    class Meta:
        model = MateriaLegislativa
        fields = '__all__'


class SessaoPlenariaSerializer(serializers.ModelSerializer):

    tipo = serializers.StringRelatedField(many=False)
    sessao_legislativa = serializers.StringRelatedField(many=False)
    legislatura = serializers.StringRelatedField(many=False)

    class Meta:
        model = SessaoPlenaria
        fields = ('pk',
                  'tipo',
                  'sessao_legislativa',
                  'legislatura',
                  'data_inicio',
                  'hora_inicio',
                  'hora_fim',
                  'url_video',
                  'iniciada',
                  'finalizada',
                  'interativa'
                  )
