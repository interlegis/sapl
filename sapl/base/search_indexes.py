import textract

from haystack import indexes
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from django.template import Context, loader


class DocumentoAcessorioIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    filename = 'arquivo'
    model = DocumentoAcessorio
    template_name = 'materia/documentoacessorio_text.txt'

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def prepare(self, obj):
        if not self.filename or not self.model or not self.template_name:
            raise Exception

        data = super(DocumentoAcessorioIndex, self).prepare(obj)

        arquivo = getattr(obj, self.filename)

        if arquivo:
            try:
                arquivo.open()
            except OSError:
                return self.prepared_data

            extracted_data = textract.process(
                arquivo.path).decode(
                'utf-8').replace('\n', ' ')

            # Now we'll finally perform the template processing to render the
            # text field with *all* of our metadata visible for templating:
            t = loader.select_template((
                'search/indexes/' + self.template_name, ))
            data['text'] = t.render(Context({'object': obj,
                                             'extracted': extracted_data}))

            return data

        return self.prepared_data


class MateriaLegislativaIndex(DocumentoAcessorioIndex):
    text = indexes.CharField(document=True, use_template=True)

    filename = 'texto_original'
    model = MateriaLegislativa
    template_name = 'materia/materialegislativa_text.txt'