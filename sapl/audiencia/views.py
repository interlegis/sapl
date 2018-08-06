from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import UpdateView
from sapl.crud.base import RP_DETAIL, RP_LIST, Crud

from .forms import AudienciaForm
from .models import AudienciaPublica


def index(request):
    return HttpResponse("Audiência  Pública")


class AudienciaCrud(Crud):
    model = AudienciaPublica
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['numero', 'nome', 'tipo', 'materia',
                            'data']
        ordering = 'nome', 'numero', 'tipo', 'data'

    class ListView(Crud.ListView):
        paginate_by = 10

    class CreateView(Crud.CreateView):
        form_class = AudienciaForm

        def form_valid(self, form):
            return super(Crud.CreateView, self).form_valid(form)

    class UpdateView(Crud.UpdateView):
        form_class = AudienciaForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['tipo_materia'] = self.object.materia.tipo.id
            initial['numero_materia'] = self.object.materia.numero
            initial['ano_materia'] = self.object.materia.ano
            return initial
     
    class DeleteView(Crud.DeleteView):
        pass

    class DetailView(Crud.DetailView):

        layout_key = 'AudienciaPublicaDetail'

        @xframe_options_exempt
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)

    