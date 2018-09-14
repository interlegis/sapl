from rest_framework import serializers
from sapl.materia.models import MateriaLegislativa


class MateriaLegislativaSerializer(serializers.ModelSerializer):

    class Meta:
        model = MateriaLegislativa
        fields = '__all__'
