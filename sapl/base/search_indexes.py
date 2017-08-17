import logging
import os.path
import re
import string

import textract
from django.template import loader
from haystack import indexes
from textract.exceptions import ExtensionNotSupported

from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.settings import BASE_DIR, SOLR_URL

logger = logging.getLogger(BASE_DIR.name)


class DocumentoAcessorioIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    filename = 'arquivo'
    model = DocumentoAcessorio
    template_name = 'materia/documentoacessorio_text.txt'

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_updated_field(self):
        return 'data_ultima_atualizacao'

    def solr_extraction(self, arquivo):
        extracted_data = self._get_backend(None).extract_file_contents(
            arquivo)['contents']
        # Remove as tags xml
        extracted_data = re.sub('<[^>]*>', '', extracted_data)
        # Remove tags \t e \n
        extracted_data = extracted_data.replace(
            '\n', ' ').replace('\t', ' ')
        # Remove sinais de pontuação
        extracted_data = re.sub('[' + string.punctuation + ']',
                                ' ', extracted_data)
        # Remove espaços múltiplos
        extracted_data = " ".join(extracted_data.split())

        return extracted_data

    def whoosh_extraction(self, arquivo):
        return textract.process(
            arquivo.path,
            language='pt-br').decode('utf-8').replace('\n', ' ').replace(
            '\t', ' ')

    def print_error(self, arquivo):
        msg = 'Erro inesperado processando arquivo: %s' % (
            arquivo.path)
        print(msg)
        logger.error(msg)

    def prepare(self, obj):
        if not self.filename or not self.model or not self.template_name:
            raise Exception

        data = super(DocumentoAcessorioIndex, self).prepare(obj)

        arquivo = getattr(obj, self.filename)

        if arquivo:
            if not os.path.exists(arquivo.path):
                return self.prepared_data

            if not os.path.splitext(arquivo.path)[1][:1]:
                return self.prepared_data

            # Em ambiente de produção utiliza-se o SOLR
            if SOLR_URL:
                try:
                    extracted_data = self.solr_extraction(arquivo)
                except Exception:
                    self.print_error(arquivo)
                    return self.prepared_data

            # Em ambiente de DEV utiliza-se o Whoosh
            # Como ele não possui extração, faz-se uso do textract
            else:
                try:
                    extracted_data = self.whoosh_extraction(arquivo)
                except ExtensionNotSupported as e:
                    print(str(e))
                    logger.error(str(e))
                    return self.prepared_data
                except Exception:
                    self.print_error(arquivo)
                    return self.prepared_data

            # Now we'll finally perform the template processing to render the
            # text field with *all* of our metadata visible for templating:
            t = loader.select_template((
                'search/indexes/' + self.template_name, ))
            data['text'] = t.render({'object': obj,
                                     'extracted': extracted_data})

            return data

        return self.prepared_data


class MateriaLegislativaIndex(DocumentoAcessorioIndex):
    text = indexes.CharField(document=True, use_template=True)

    filename = 'texto_original'
    model = MateriaLegislativa
    template_name = 'materia/materialegislativa_text.txt'

    def get_updated_field(self):
        return 'data_ultima_atualizacao'


class NormaJuridicaIndex(DocumentoAcessorioIndex):
    text = indexes.CharField(document=True, use_template=True)

    filename = 'texto_integral'
    model = NormaJuridica
    template_name = 'norma/normajuridica_text.txt'

    def get_updated_field(self):
        return 'data_ultima_atualizacao'
