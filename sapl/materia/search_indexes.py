
from haystack import indexes
from sapl.materia.models import DocumentoAcessorio

class DocumentoAcessorioIndex(indexes.SearchIndex, indexes.Indexable):
    text  = indexes.CharField(document=True, use_template=True)
    nome  = indexes.CharField(model_attr='nome')
    autor = indexes.CharField(model_attr='autor')

#    def prepare(self, obj):
#       data = super(DocumentoAcessorioIndex, self).prepare(obj)
#       if obj.arquivo is not None:
#            file_data = self._get_backend(None).extract_file_contents(
#                obj.arquivo,
#            )
#           template = loader.select_template(
#                ("search/indexes/materia/documentoacessorio_text.txt", ),
#           )
#
#           data["text"] = template.render(Context({
#                "object": obj,
#                "file_data": file_data,
#            }))
#
#       return data

    def get_model(self):
        return DocumentoAcessorio

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
