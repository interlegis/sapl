import logging

from django.conf import settings
from rest_framework import serializers
from rest_framework.relations import StringRelatedField

from sapl.base.models import CasaLegislativa


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


class CasaLegislativaSerializer(serializers.ModelSerializer):
    version = serializers.SerializerMethodField()

    def get_version(self, obj):
        return settings.SAPL_VERSION

    class Meta:
        model = CasaLegislativa
        fields = '__all__'
