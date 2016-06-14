from django.views.generic.base import TemplateView

from sapl.crud.base import Crud, CrudBaseMixin, CrudCreateView, CrudUpdateView

from .forms import CasaLegislativaForm
from .models import CasaLegislativa


def get_casalegislativa():
    return CasaLegislativa.objects.first()


class CasaLegislativaCrud(Crud):
    model = CasaLegislativa
    help_path = ''

    class BaseMixin(CrudBaseMixin):
        list_field_names = ['codigo', 'nome', 'sigla']

    class CreateView(CrudCreateView):
        form_class = CasaLegislativaForm

    class UpdateView(CrudUpdateView):
        form_class = CasaLegislativaForm


class HelpView(TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        return ['ajuda/%s.html' % self.kwargs['topic']]
