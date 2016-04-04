import os
from functools import lru_cache

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.views.generic import FormView
from django.views.generic.base import TemplateView

from .forms import CasaLegislativaTabelaAuxForm
from .models import CasaLegislativa


@lru_cache(maxsize=1)
def get_casalegislativa():
    return CasaLegislativa.objects.first()


class HelpView(TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        return ['ajuda/%s.html' % self.kwargs['topic']]


class CasaLegislativaTableAuxView(FormView):

    template_name = "base/casa_leg_table_aux.html"

    def get(self, request, *args, **kwargs):
        try:
            casa = CasaLegislativa.objects.first()
        except ObjectDoesNotExist:
            form = CasaLegislativaTabelaAuxForm()
        else:
            form = CasaLegislativaTabelaAuxForm(instance=casa)

        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = CasaLegislativaTabelaAuxForm(request.POST, request.FILES)
        if form.is_valid():
            casa = CasaLegislativa.objects.first()
            if casa:
                if ("remover" in request.POST or
                   (form.cleaned_data['logotipo'] and casa.logotipo)):
                    try:
                        os.unlink(casa.logotipo.path)
                    except OSError:
                        pass  # Should log this error!!!!!
                    casa.logotipo = None
                CasaLegislativaTabelaAuxForm(
                    request.POST,
                    request.FILES,
                    instance=casa
                ).save()
            else:
                form.save()

            # Invalida cache de consulta
            get_casalegislativa.cache_clear()

            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form})

    def get_success_url(self):
        return reverse('base:casa_legislativa')
