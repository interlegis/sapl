from django.shortcuts import render, get_object_or_404, redirect
from .models import ConfiguracaoImpressao
from .forms import ConfiguracaoImpressaoForm
from sapl.crud.base import Crud, MasterDetailCrud
import os


class ConfiguracaoImpressaoCrud(Crud):
    model = ConfiguracaoImpressao

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['identificador', 'nome', 'descricao']

    class CreateView(Crud.CreateView):
        form_class = ConfiguracaoImpressaoForm

        def form_valid(self, form):
            return super(Crud.CreateView, self).form_valid(form)

    class UpdateView(Crud.UpdateView):
        form_class = ConfiguracaoImpressaoForm

        def get_initial(self):
            initial = super().get_initial()
            initial['identificador'] = self.object.identificador
            return initial

    class DetailView(Crud.DetailView):
        layout_key = 'ConfiguracaoImpressaoDetail'

    class ListView(Crud.ListView):
        paginate_by = None
        ordering = ['identificador', 'nome']
