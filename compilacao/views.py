from collections import OrderedDict
from datetime import datetime, timedelta
from os.path import sys

from braces.views import FormMessagesMixin
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
from django.views.generic.edit import FormMixin, UpdateView, CreateView,\
    DeleteView
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
    'dispositivo_atualizador__dispositivo_pai__ta__tipo_ta',
    'dispositivo_pai',
    'dispositivo_pai__tipo_dispositivo')


class TaListView(ListView):
    model = TextoArticulado
    paginate_by = 10
    verbose_name = model._meta.verbose_name
    title = model._meta.verbose_name_plural
    create_url = reverse_lazy('ta_create')

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


class TaCreateView(FormMessagesMixin, CreateView):
    model = TextoArticulado
    form_class = forms.TaForm
    template_name = "compilacao/form.html"
    form_valid_message = _('Registro criado com sucesso!')
    form_invalid_message = _('O registro não foi criado.')

    def get_success_url(self):
        return reverse_lazy('ta_detail', kwargs={'pk': self.object.id})


class TaUpdateView(UpdateView):
    model = TextoArticulado
    form_class = forms.TaForm
    template_name = "compilacao/form.html"

    @property
    def title(self):
        return self.get_object()

    def get_success_url(self):
        return reverse_lazy('ta_detail', kwargs={'pk': self.kwargs['pk']})


class TaDeleteView(DeleteView):
    model = TextoArticulado

    @property
    def title(self):
        return self.get_object()

    @property
    def detail_url(self):
        return reverse_lazy('ta_detail', kwargs={'pk': self.kwargs['pk']})

    def get_success_url(self):
        return reverse_lazy('ta_list')


class TextoView(ListView):
    template_name = 'compilacao/text_list.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    itens_de_vigencia = {}

    inicio_vigencia = None
    fim_vigencia = None

    def get_context_data(self, **kwargs):
        context = super(TextoView, self).get_context_data(**kwargs)

        cita = Vide.objects.filter(
            Q(dispositivo_base__ta_id=self.kwargs['ta_id'])).\
            select_related(
            'dispositivo_ref',
            'dispositivo_ref__ta',
            'dispositivo_ref__dispositivo_pai',
            'dispositivo_ref__dispositivo_pai__ta', 'tipo')

        context['cita'] = {}
        for c in cita:
            if str(c.dispositivo_base_id) not in context['cita']:
                context['cita'][str(c.dispositivo_base_id)] = []
            context['cita'][str(c.dispositivo_base_id)].append(c)

        citado = Vide.objects.filter(
            Q(dispositivo_ref__ta_id=self.kwargs['ta_id'])).\
            select_related(
            'dispositivo_base',
            'dispositivo_base__ta',
            'dispositivo_base__dispositivo_pai',
            'dispositivo_base__dispositivo_pai__ta', 'tipo')

        context['citado'] = {}
        for c in citado:
            if str(c.dispositivo_ref_id) not in context['citado']:
                context['citado'][str(c.dispositivo_ref_id)] = []
            context['citado'][str(c.dispositivo_ref_id)].append(c)

        notas = Nota.objects.filter(
            dispositivo__ta_id=self.kwargs['ta_id']).select_related(
            'owner', 'tipo')

        context['notas'] = {}
        for n in notas:
            if str(n.dispositivo_id) not in context['notas']:
                context['notas'][str(n.dispositivo_id)] = []
            context['notas'][str(n.dispositivo_id)].append(n)
        return context

    def get_queryset(self):
        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1

        self.inicio_vigencia = None
        self.fim_vigencia = None
        if 'sign' in self.kwargs:
            signer = Signer()
            try:
                string = signer.unsign(self.kwargs['sign']).split(',')
                self.inicio_vigencia = parse_date(string[0])
                self.fim_vigencia = parse_date(string[1])
            except:
                return{}

            return Dispositivo.objects.filter(
                inicio_vigencia__lte=self.fim_vigencia,
                ordem__gt=0,
                ta_id=self.kwargs['ta_id'],
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        else:

            r = Dispositivo.objects.filter(
                ordem__gt=0,
                ta_id=self.kwargs['ta_id'],
            ).select_related(
                'tipo_dispositivo',
                'ta_publicado',
                'ta',
                'dispositivo_atualizador',
                'dispositivo_atualizador__dispositivo_pai',
                'dispositivo_atualizador__dispositivo_pai__ta',
                'dispositivo_atualizador__dispositivo_pai__ta__tipo_ta',
                'dispositivo_pai',
                'dispositivo_pai__tipo_dispositivo')

            return r

    def get_vigencias(self):
        itens = Dispositivo.objects.filter(
            ta_id=self.kwargs['ta_id'],
        ).order_by(
            'inicio_vigencia'
        ).distinct(
            'inicio_vigencia'
        ).select_related(
            'ta_publicado',
            'ta',
            'ta_publicado__tipo_ta',
            'ta__tipo_ta',)

        ajuste_datas_vigencia = []

        for item in itens:
            ajuste_datas_vigencia.append(item)

        lenLista = len(ajuste_datas_vigencia)
        for i in range(lenLista):
            if i + 1 < lenLista:
                ajuste_datas_vigencia[
                    i].fim_vigencia = ajuste_datas_vigencia[
                        i + 1].inicio_vigencia - timedelta(days=1)
            else:
                ajuste_datas_vigencia[i].fim_vigencia = None

        self.itens_de_vigencia = {}

        idx = -1
        length = len(ajuste_datas_vigencia)
        for item in ajuste_datas_vigencia:
            idx += 1
            if idx == 0:
                self.itens_de_vigencia[0] = [item, ]
                continue

            if idx + 1 < length:
                ano = item.ta_publicado.ano
                if ano in self.itens_de_vigencia:
                    self.itens_de_vigencia[ano].append(item)
                else:
                    self.itens_de_vigencia[ano] = [item, ]
            else:
                self.itens_de_vigencia[9999] = [item, ]

        if len(self.itens_de_vigencia.keys()) <= 1:
            return {}

        self.itens_de_vigencia = OrderedDict(
            sorted(self.itens_de_vigencia.items(), key=lambda t: t[0]))

        return self.itens_de_vigencia

    def get_ta(self):
        return TextoArticulado.objects.select_related('tipo_ta').get(
            pk=self.kwargs['ta_id'])

    def is_ta_alterador(self):
        if self.flag_alteradora == -1:
            self.flag_alteradora = Dispositivo.objects.select_related(
                'dispositivos_alterados_pelo_texto_articulado_set'
            ).filter(ta_id=self.kwargs['ta_id']).count()
        return self.flag_alteradora > 0


class DispositivoView(TextoView):
    # template_name = 'compilacao/index.html'
    template_name = 'compilacao/text_list_bloco.html'

    def get_queryset(self):
        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1

        try:
            bloco = Dispositivo.objects.get(pk=self.kwargs['dispositivo_id'])
        except Dispositivo.DoesNotExist:
            return []

        self.flag_nivel_old = bloco.nivel - 1
        self.flag_nivel_ini = bloco.nivel

        proximo_bloco = Dispositivo.objects.filter(
            ordem__gt=bloco.ordem,
            nivel__lte=bloco.nivel,
            ta_id=self.kwargs['ta_id'])[:1]

        if proximo_bloco.count() == 0:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                ta_id=self.kwargs['ta_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        else:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                ordem__lt=proximo_bloco[0].ordem,
                ta_id=self.kwargs['ta_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        return itens
