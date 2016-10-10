from rest_framework import serializers

from sapl.comissoes.models import Comissao
from sapl.parlamentares.models import Parlamentar


class ChoiceSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    display = serializers.SerializerMethodField()

    def get_display(self, obj):
        return str(obj)
"""

class ModelChoiceParlamentarSerializer(ModelChoiceSerializer):

    class Meta:
        model = Parlamentar


class ModelChoiceComissaoSerializer(ModelChoiceSerializer):

    class Meta:
        model = Comissao
"""