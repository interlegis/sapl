import os
from functools import lru_cache

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.views.generic import FormView
from django.views.generic.base import TemplateView

import crud.base
from crud.base import Crud

from .forms import CasaLegislativaForm
from .models import CasaLegislativa


# @lru_cache(maxsize=1)
def get_casalegislativa():
    return CasaLegislativa.objects.first()


class CasaLegislativaCrud(Crud):
    model = CasaLegislativa
    help_path = ''

    class BaseMixin(crud.base.CrudBaseMixin):
        list_field_names = ['codigo', 'nome', 'sigla']

    class CreateView(crud.base.CrudCreateView):
        form_class = CasaLegislativaForm

    class UpdateView(crud.base.CrudUpdateView):
        form_class = CasaLegislativaForm


class HelpView(TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        return ['ajuda/%s.html' % self.kwargs['topic']]
