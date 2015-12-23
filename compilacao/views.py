from collections import OrderedDict
from datetime import datetime, timedelta
from os.path import sys

from django.contrib.auth.decorators import login_required
from django.contrib.messages.api import success
from django.core.signing import Signer
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http.response import (HttpResponse, HttpResponseRedirect,
                                  JsonResponse)
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin, UpdateView, CreateView
from django.views.generic.list import ListView

from compilacao import forms, utils
from compilacao.models import (Dispositivo, Nota,
                               PerfilEstruturalTextoArticulado,
                               TipoDispositivo, TipoNota, TipoPublicacao,
                               TipoVide, VeiculoPublicacao, Vide,
                               TextoArticulado)


DISPOSITIVO_SELECT_RELATED = (
    'tipo_dispositivo',
    'ta_publicado',
    'ta',
    'dispositivo_atualizador',
    'dispositivo_atualizador__dispositivo_pai',
    'dispositivo_atualizador__dispositivo_pai__ta',
    'dispositivo_atualizador__dispositivo_pai__ta__tipo',
    'dispositivo_pai',
    'dispositivo_pai__tipo_dispositivo')


class TaListView(ListView):
    model = TextoArticulado
    paginate_by = 10
    title = TextoArticulado._meta.verbose_name_plural

    def get_context_data(self, **kwargs):
        context = super(TaListView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = utils.make_pagination(
            page_obj.number, paginator.num_pages)
        return context


class TaDetailView(DetailView):
    model = TextoArticulado

    @property
    def title(self):
        return self.get_object()


class TaUpdateView(UpdateView):
    model = TextoArticulado
    form_class = forms.TaForm
    template_name = "compilacao/form.html"

    @property
    def title(self):
        return self.get_object()

    def get_success_url(self):
        return reverse_lazy('ta_detail', kwargs={'pk': self.kwargs['pk']})
