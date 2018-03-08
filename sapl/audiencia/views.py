from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.db.models import F
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import ListView
from sapl.comissoes.forms import ParticipacaoCreateForm, ParticipacaoEditForm
from sapl.crud.base import RP_DETAIL, RP_LIST, Crud, CrudAux, MasterDetailCrud
from sapl.materia.models import MateriaLegislativa

from .forms import AudienciaForm
from .models import (AudienciaPublica, TipoAudienciaPublica)

def index(request):
    return HttpResponse("Audiência  Pública")

class AudienciaCrud(Crud):
    model = AudienciaPublica
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['materia', 'tipo', 'numero', 'nome',
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
            self.initial['tipo_materia'] = self.object.materia.tipo.id
            self.initial['numero_materia'] = self.object.materia.numero
            self.initial['ano_materia'] = self.object.materia.ano
            return self.initial
     
    class DeleteView(Crud.DeleteView):
        pass

    class DetailView(Crud.DetailView):

        layout_key = 'AudienciaPublicaDetail'

        @xframe_options_exempt
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)

    