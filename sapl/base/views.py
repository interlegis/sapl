from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView

from sapl.crud.base import (Crud, CrudBaseMixin, CrudCreateView,
                            CrudDetailView, CrudUpdateView)

from .forms import CasaLegislativaForm
from .models import CasaLegislativa


def get_casalegislativa():
    return CasaLegislativa.objects.first()


class CasaLegislativaCrud(Crud):
    model = CasaLegislativa
    help_path = ''

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        permission_required = {'base.add_casalegislativa'}
        list_field_names = ['codigo', 'nome', 'sigla']

    class CreateView(PermissionRequiredMixin, CrudCreateView):
        permission_required = {'base.add_casa_legislativa'}
        form_class = CasaLegislativaForm

    class UpdateView(PermissionRequiredMixin, CrudUpdateView):
        permission_required = {'base.change_casalegislativa'}
        form_class = CasaLegislativaForm

    class DetailView(CrudDetailView):
        form_class = CasaLegislativaForm

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(
                reverse('sapl.base:casalegislativa_update',
                        kwargs={'pk': self.kwargs['pk']}))


class HelpView(PermissionRequiredMixin, TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        return ['ajuda/%s.html' % self.kwargs['topic']]
