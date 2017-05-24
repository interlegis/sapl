import logging
import os.path

import textract
from django.template import Context, loader
from haystack import indexes

from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.norma.models import NormaJuridica

from textract.exceptions import ExtensionNotSupported

from sapl.settings import BASE_DIR
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

            try:
                extracted_data = textract.process(
                    arquivo.path,
                    language='pt-br').decode('utf-8').replace('\n', ' ')
            except ExtensionNotSupported:
                return self.prepared_data
            except Exception:
                msg = 'Erro inesperado processando arquivo: %s' % arquivo.path
                print(msg)
                logger.error(msg)
                return self.prepared_data

            extracted_data = extracted_data.replace('\t', ' ')

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


class NormaJuridicaIndex(DocumentoAcessorioIndex):
    text = indexes.CharField(document=True, use_template=True)

    filename = 'texto_integral'
    model = NormaJuridica
    template_name = 'norma/normajuridica_text.txt'
