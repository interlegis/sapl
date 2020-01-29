import logging
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import F, Q
from rest_framework import serializers
from rest_framework.relations import StringRelatedField
from sapl.parlamentares.models import Parlamentar, Mandato, Filiacao, Legislatura
from sapl.base.models import Autor, CasaLegislativa
from sapl.utils import filiacao_data
from image_cropping.utils import get_backend


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
    fotografia_cropped = serializers.SerializerMethodField('crop_fotografia')
    logger = logging.getLogger(__name__)

    def crop_fotografia(self,obj):
        thumbnail_url = ""
        try:
            import os
            #import pdb;pdb.set_trace()
            if not obj.fotografia or not os.path.exists(obj.fotografia.path):
                return thumbnail_url
            thumbnail_url = get_backend().get_thumbnail_url( 
                obj.fotografia, 
                { 
                    'size': (128, 128), 
                    'box': obj.cropping, 
                    'crop': True, 
                    'detail': True, 
                } 
            )
        except Exception as e:
            self.logger.error(e)
            self.logger.error('erro processando arquivo: %s' % obj.fotografia.path)
        
        return thumbnail_url

    def check_titular(self,obj):
        is_titular = None
        if not Legislatura.objects.exists():
            self.logger.error("Não há legislaturas cadastradas.")
            return ""
        
        try:
            legislatura = Legislatura.objects.get(id=self.context.get('legislatura'))
        except ObjectDoesNotExist:
            legislatura = Legislatura.objects.first()
        mandato = Mandato.objects.filter(
            parlamentar=obj,
            data_inicio_mandato__gte=legislatura.data_inicio,
            data_fim_mandato__lte=legislatura.data_fim
        ).order_by('-data_inicio_mandato').first()
        if mandato:
            is_titular = 'Sim' if mandato.titular else 'Não'
        else:
            is_titular = '-'        
        return is_titular

    def check_partido(self,obj):
        # Coloca a filiação atual ao invés da última
        # As condições para mostrar a filiação são:
        # A data de filiacao deve ser menor que a data de fim
        # da legislatura e data de desfiliação deve nula, ou maior,
        # ou igual a data de fim da legislatura
        
        username =  self.context['request'].user.username
        if not Legislatura.objects.exists():
            self.logger.error("Não há legislaturas cadastradas.")
            return ""
        try:
            legislatura = Legislatura.objects.get(id=self.context.get('legislatura'))
        except ObjectDoesNotExist:
            legislatura = Legislatura.objects.first()
    
        try:
            self.logger.debug("user=" + username + ". Tentando obter filiação do parlamentar com (data<={} e data_desfiliacao>={}) "
                              "ou (data<={} e data_desfiliacao=Null))."
                              .format(legislatura.data_fim, legislatura.data_fim, legislatura.data_fim))
            filiacao = obj.filiacao_set.get(Q(
                data__lte=legislatura.data_fim,
                data_desfiliacao__gte=legislatura.data_fim) | Q(
                data__lte=legislatura.data_fim,
                data_desfiliacao__isnull=True))

        # Caso não exista filiação com essas condições
        except ObjectDoesNotExist:
            self.logger.error("user=" + username + ". Parlamentar com (data<={} e data_desfiliacao>={}) "
                              "ou (data<={} e data_desfiliacao=Null)) não possui filiação."
                              .format(legislatura.data_fim, legislatura.data_fim, legislatura.data_fim))
            filiacao = 'Não possui filiação'

        # Caso exista mais de uma filiação nesse intervalo
        # Entretanto, NÃO DEVE OCORRER
        except MultipleObjectsReturned:
            self.logger.error("user=" + username + ". O Parlamentar com (data<={} e data_desfiliacao>={}) "
                              "ou (data<={} e data_desfiliacao=Null)) possui duas filiações conflitantes"
                              .format(legislatura.data_fim, legislatura.data_fim, legislatura.data_fim))
            filiacao = 'O Parlamentar possui duas filiações conflitantes'

        # Caso encontre UMA filiação nessas condições
        else:
            self.logger.debug("user=" + username +
                              ". Filiação encontrada com sucesso.")
            filiacao = filiacao.partido.sigla
        
        return filiacao

    class Meta:
        model = Parlamentar
        fields = ['id', 'nome_parlamentar', 'fotografia_cropped','fotografia', 'ativo', 'partido', 'titular']
