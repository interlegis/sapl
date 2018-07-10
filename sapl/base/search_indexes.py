import logging
import os.path
import re
import string

import textract
from django.db.models import F, Q, Value
from django.db.models.fields import TextField
from django.db.models.fields.files import FieldFile
from django.db.models.functions import Concat
from django.template import loader
from haystack.constants import Indexable
from haystack.fields import CharField
from haystack.indexes import SearchIndex
from haystack.utils import get_model_ct_tuple
from textract.exceptions import ExtensionNotSupported

from sapl.compilacao.models import (STATUS_TA_IMMUTABLE_PUBLIC,
                                    STATUS_TA_PUBLIC, Dispositivo,
                                    TextoArticulado)
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.settings import BASE_DIR, SOLR_URL
from sapl.utils import RemoveTag

logger = logging.getLogger(BASE_DIR.name)


class TextExtractField(CharField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert self.model_attr

        if not isinstance(self.model_attr, (list, tuple)):
            self.model_attr = (self.model_attr, )

    def solr_extraction(self, arquivo):
        return textract.process(
            arquivo.path,
            language='pt-br').decode('utf-8').replace('\n', ' ').replace(
            '\t', ' ')

    def whoosh_extraction(self, arquivo):

        if arquivo.path.endswith('html') or arquivo.path.endswith('xml'):
            with open(arquivo.path, 'r', encoding="utf8", errors='ignore') as f:
                content = ' '.join(f.read())
                return RemoveTag(content)

        else:
            return textract.process(
                arquivo.path,
                language='pt-br').decode('utf-8').replace('\n', ' ').replace(
                '\t', ' ')

    def print_error(self, arquivo, error):
        msg = 'Erro inesperado processando arquivo %s erro: %s' % (
            arquivo.path, error)
        print(msg, error)
        logger.error(msg, error)

    def file_extractor(self, arquivo):
        if not os.path.exists(arquivo.path) or \
                not os.path.splitext(arquivo.path)[1][:1]:
            return ''

        # Em ambiente de produção utiliza-se o SOLR
        if SOLR_URL:
            try:
                return self.solr_extraction(arquivo)
            except Exception as err:
                print(str(err))
                self.print_error(arquivo, err)

        # Em ambiente de DEV utiliza-se o Whoosh
        # Como ele não possui extração, faz-se uso do textract
        else:
            try:
                return self.whoosh_extraction(arquivo)
            except ExtensionNotSupported as err:
                print(str(err))
                logger.error(str(err))
            except Exception as err:
                print(str(err))
                self.print_error(arquivo, str(err))
        return ''

    def ta_extractor(self, value):
        r = []
        for ta in value.filter(privacidade__in=[
                STATUS_TA_PUBLIC,
                STATUS_TA_IMMUTABLE_PUBLIC]):
            dispositivos = Dispositivo.objects.filter(
                Q(ta=ta) | Q(ta_publicado=ta)
            ).order_by(
                'ordem'
            ).annotate(
                rotulo_texto=Concat(
                    F('rotulo'), Value(' '), F('texto'),
                    output_field=TextField(),
                )
            ).values_list(
                'rotulo_texto', flat=True)
            r += list(filter(lambda x: x.strip(), dispositivos))
        return ' '.join(r)

    def string_extractor(self, value):
        return value

    def extract_data(self, obj):

        data = ''

        for attr, func in self.model_attr:
            if not hasattr(obj, attr) or not hasattr(self, func):
                raise Exception

            value = getattr(obj, attr)
            if not value:
                continue
            data += getattr(self, func)(value)

        return data

    def prepare_template(self, obj):
        app_label, model_name = get_model_ct_tuple(obj)
        template_names = ['search/indexes/%s/%s_%s.txt' %
                          (app_label, model_name, self.instance_name)]

        t = loader.select_template(template_names)

        return t.render({'object': obj,
                         'extracted': self.extract_data(obj)})


class DocumentoAcessorioIndex(SearchIndex, Indexable):
    model = DocumentoAcessorio
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('arquivo', 'file_extractor'),
            ('ementa', 'string_extractor'),
            ('indexacao', 'string_extractor'),
        )
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text.search_index = self

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_updated_field(self):
        return 'data_ultima_atualizacao'


class NormaJuridicaIndex(DocumentoAcessorioIndex):
    model = NormaJuridica
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('texto_integral', 'file_extractor'),
            ('texto_articulado', 'ta_extractor'),
            ('ementa', 'string_extractor'),
            ('indexacao', 'string_extractor'),
            ('observacao', 'string_extractor'),
        )
    )


class MateriaLegislativaIndex(DocumentoAcessorioIndex):
    model = MateriaLegislativa
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('texto_original', 'file_extractor'),
            ('texto_articulado', 'ta_extractor'),
            ('ementa', 'string_extractor'),
            ('indexacao', 'string_extractor'),
            ('observacao', 'string_extractor'),
        )
    )
