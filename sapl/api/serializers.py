import logging

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q
from image_cropping.utils import get_backend
from rest_framework import serializers

from sapl.api.core.serializers import ModelChoiceObjectRelatedField
from sapl.base.models import Autor
from sapl.parlamentares.models import Parlamentar, Mandato, Legislatura


class AutorSerializer(serializers.ModelSerializer):
    # AutorSerializer sendo utilizado pelo gerador automático da api devidos aos
    # critérios anotados em views.py

    autor_related = ModelChoiceObjectRelatedField(read_only=True)

    class Meta:
        model = Autor
        fields = '__all__'


class ParlamentarSerializerPublic(serializers.ModelSerializer):

    class Meta:
        model = Parlamentar
        exclude = ["cpf", "rg", "fax",
                   "endereco_residencia", "municipio_residencia",
                   "uf_residencia", "cep_residencia", "situacao_militar",
                   "telefone_residencia", "titulo_eleitor", "fax_residencia"]


class ParlamentarSerializerVerbose(serializers.ModelSerializer):
    titular = serializers.SerializerMethodField('check_titular')
    partido = serializers.SerializerMethodField('check_partido')
    fotografia_cropped = serializers.SerializerMethodField('crop_fotografia')
    logger = logging.getLogger(__name__)

    def crop_fotografia(self, obj):
        thumbnail_url = ""
        try:
            import os
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

    def check_titular(self, obj):
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

    def check_partido(self, obj):
        # Coloca a filiação atual ao invés da última
        # As condições para mostrar a filiação são:
        # A data de filiacao deve ser menor que a data de fim
        # da legislatura e data de desfiliação deve nula, ou maior,
        # ou igual a data de fim da legislatura

        username = self.context['request'].user.username
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
            self.logger.warning("user=" + username + ". Parlamentar com (data<={} e data_desfiliacao>={}) "
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
        fields = ['id', 'nome_parlamentar', 'fotografia_cropped', 'fotografia', 'ativo', 'partido', 'titular']
