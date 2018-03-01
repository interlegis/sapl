from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.db.models import F
from django.views.generic import ListView
from sapl.comissoes.forms import ParticipacaoCreateForm, ParticipacaoEditForm
from sapl.crud.base import RP_DETAIL, RP_LIST, Crud, CrudAux, MasterDetailCrud
from sapl.materia.models import MateriaLegislativa

from .forms import AudienciaForm
from .models import (AudienciaPublica, TipoAudienciaPublica)

def index(request):
    return HttpResponse("Audiência Pública")

class AudienciaCrud(Crud):
    model = AudienciaPublica
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['materia', 'tipo', 'numero', 'nome', 'tema',
                            'data', 'hora_inicio', 'hora_fim', 'observacao',
                            'url_audio', 'url_video', 'upload_pauta',
                            'upload_ata']
        ordering = 'nome', 'numero', 'tipo', 'data'

    class CreateView(Crud.CreateView):
        form_class = AudienciaForm

        def form_valid(self, form):
            return super(Crud.CreateView, self).form_valid(form)