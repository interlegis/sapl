from django.conf import settings
from rest_framework import serializers
from rest_framework.relations import StringRelatedField
from sapl.parlamentares.models import Parlamentar, Mandato, Filiacao, Legislatura
from sapl.base.models import Autor, CasaLegislativa
from sapl.utils import filiacao_data

class IntRelatedField(StringRelatedField):
    def to_representation(self, value):
        return int(value)


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


class AutorSerializer(serializers.ModelSerializer):
    # AutorSerializer sendo utilizado pelo gerador automático da api devidos aos
    # critérios anotados em views.py

    autor_related = ModelChoiceObjectRelatedField(read_only=True)

    class Meta:
        model = Autor
        fields = '__all__'


class CasaLegislativaSerializer(serializers.ModelSerializer):
    version = serializers.SerializerMethodField()

    def get_version(self, obj):
        return settings.SAPL_VERSION

    class Meta:
        model = CasaLegislativa
        fields = '__all__'

class ParlamentarResumeSerializer(serializers.ModelSerializer):
    titular = serializers.SerializerMethodField('check_titular')
    partido = serializers.SerializerMethodField('check_partido')

    def check_titular(self,obj):
        legislatura = self.context.get('legislatura')
        if not legislatura:
            legislatura = Legislatura.objects.first().id
        mandato = Mandato.objects.filter(legislatura__id=legislatura,parlamentar=obj).first()
        return mandato.titular if mandato else False

    def check_partido(self,obj):
        legislatura_id = self.context.get('legislatura')
        if not legislatura_id:
            legislatura = Legislatura.objects.first()
        else:
            legislatura = Legislatura.objects.get(id=legislatura_id)
        filiacao = filiacao_data(obj, legislatura.data_inicio, legislatura.data_fim)
        return filiacao

    class Meta:
        model = Parlamentar
        fields = ['id', 'nome_parlamentar', 'fotografia', 'ativo', 'partido', 'titular']
