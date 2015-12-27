from collections import OrderedDict
from datetime import datetime, timedelta

from braces.views import FormMessagesMixin
from django.contrib.auth.decorators import login_required
from django.core.signing import Signer
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from compilacao import forms, utils
from compilacao.models import (Dispositivo, Nota,
                               PerfilEstruturalTextoArticulado,
                               TextoArticulado, TipoDispositivo, TipoNota,
                               Vide)

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


class TextView(ListView):
    template_name = 'compilacao/text_list.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    itens_de_vigencia = {}

    inicio_vigencia = None
    fim_vigencia = None

    def get_context_data(self, **kwargs):
        context = super(TextView, self).get_context_data(**kwargs)

        context['object'] = TextoArticulado.objects.get(
            pk=self.kwargs['ta_id'])

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
            ).select_related(*DISPOSITIVO_SELECT_RELATED)

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


class DispositivoView(TextView):
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


class TextEditView(TextView):

    template_name = 'compilacao/text_edit.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    pk_edit = 0
    pk_view = 0
    """
    def get(self, request, *args, **kwargs):

        self.object_list = self.get_queryset()
        context = self.get_context_data(
            object_list=self.object_list)

        return self.render_to_response(context)"""

    def get_queryset(self):
        self.pk_edit = 0
        self.pk_view = 0

        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1

        result = Dispositivo.objects.filter(
            ta_id=self.kwargs['ta_id']
        ).select_related(*DISPOSITIVO_SELECT_RELATED)

        if not result.exists():

            ta = TextoArticulado.objects.get(pk=self.kwargs['ta_id'])

            td = TipoDispositivo.objects.filter(class_css='articulacao')[0]
            a = Dispositivo()
            a.nivel = 0
            a.ordem = Dispositivo.INTERVALO_ORDEM
            a.ordem_bloco_atualizador = 0
            a.set_numero_completo([1, 0, 0, 0, 0, 0, ])
            a.ta = ta
            a.tipo_dispositivo = td
            a.inicio_vigencia = ta.data
            a.inicio_eficacia = ta.data
            a.timestamp = datetime.now()
            a.save()

            td = TipoDispositivo.objects.filter(class_css='ementa')[0]
            e = Dispositivo()
            e.nivel = 1
            e.ordem = a.ordem + Dispositivo.INTERVALO_ORDEM
            e.ordem_bloco_atualizador = 0
            e.set_numero_completo([1, 0, 0, 0, 0, 0, ])
            e.ta = ta
            e.tipo_dispositivo = td
            e.inicio_vigencia = ta.data
            e.inicio_eficacia = ta.data
            e.timestamp = datetime.now()
            e.texto = ta.ementa
            e.dispositivo_pai = a
            e.save()

            a.pk = None
            a.nivel = 0
            a.ordem = e.ordem + Dispositivo.INTERVALO_ORDEM
            a.ordem_bloco_atualizador = 0
            a.set_numero_completo([2, 0, 0, 0, 0, 0, ])
            a.timestamp = datetime.now()
            a.save()

            result = Dispositivo.objects.filter(
                ta_id=self.kwargs['ta_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)

        return result

    def set_perfil_in_session(self, request=None, perfil_id=0):
        if not request:
            return None

        if perfil_id:
            perfil = PerfilEstruturalTextoArticulado.objects.get(
                pk=perfil_id)
            request.session['perfil_estrutural'] = perfil.pk
        else:
            perfis = PerfilEstruturalTextoArticulado.objects.filter(
                padrao=True)[:1]

            if not perfis.exists():
                request.session.pop('perfil_estrutural')
            else:
                request.session['perfil_estrutural'] = perfis[0].pk


class DispositivoSuccessUrlMixin(object):

    def get_success_url(self):
        return reverse(
            'dispositivo', kwargs={
                'ta_id': self.kwargs[
                    'ta_id'],
                'dispositivo_id': self.kwargs[
                    'dispositivo_id']})


class NotaMixin(DispositivoSuccessUrlMixin):

    def get_modelo_nota(self, request):
        if 'action' in request.GET and request.GET['action'] == 'modelo_nota':
            tn = TipoNota.objects.get(pk=request.GET['id_tipo'])
            return True, tn.modelo
        return False, ''

    def get_initial(self):
        dispositivo = get_object_or_404(
            Dispositivo, pk=self.kwargs.get('dispositivo_id'))
        initial = {'dispositivo': dispositivo}

        if 'pk' in self.kwargs:
            initial['pk'] = self.kwargs.get('pk')

        return initial

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(NotaMixin, self).dispatch(*args, **kwargs)


class NotasCreateView(NotaMixin, CreateView):
    template_name = 'compilacao/ajax_form.html'
    form_class = forms.NotaForm

    def get(self, request, *args, **kwargs):
        flag_action, modelo_nota = self.get_modelo_nota(request)
        if flag_action:
            return HttpResponse(modelo_nota)

        return super(NotasCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            ta_id = kwargs.pop('ta_id')
            dispositivo_id = kwargs.pop('dispositivo_id')
            form = forms.NotaForm(request.POST, request.FILES, **kwargs)
            kwargs['ta_id'] = ta_id
            kwargs['dispositivo_id'] = dispositivo_id

            if form.is_valid():
                nt = form.save(commit=False)
                nt.owner_id = request.user.pk
                nt.save()
                self.kwargs['pk'] = nt.pk
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        except Exception as e:
            print(e)
        return HttpResponse("error post")


class NotasEditView(NotaMixin, UpdateView):
    model = Nota
    template_name = 'compilacao/ajax_form.html'
    form_class = forms.NotaForm

    def get(self, request, *args, **kwargs):
        flag_action, modelo_nota = self.get_modelo_nota(request)
        if flag_action:
            return HttpResponse(modelo_nota)

        return super(NotasEditView, self).get(request, *args, **kwargs)


class NotasDeleteView(NotaMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        nt = Nota.objects.get(pk=self.kwargs['pk'])
        nt.delete()
        return HttpResponseRedirect(self.get_success_url())


class VideMixin(DispositivoSuccessUrlMixin):

    def get_initial(self):
        dispositivo_base = get_object_or_404(
            Dispositivo, pk=self.kwargs.get('dispositivo_id'))

        initial = {'dispositivo_base': dispositivo_base}

        if 'pk' in self.kwargs:
            initial['pk'] = self.kwargs.get('pk')

        return initial

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(VideMixin, self).dispatch(*args, **kwargs)


class VideCreateView(VideMixin, CreateView):
    model = Vide
    template_name = 'compilacao/ajax_form.html'
    form_class = forms.VideForm

    def post_old(self, request, *args, **kwargs):
        try:
            self.object = None
            ta_id = kwargs.pop('ta_id')
            dispositivo_id = kwargs.pop('dispositivo_id')
            form = forms.VideForm(request.POST, request.FILES, **kwargs)
            kwargs['ta_id'] = ta_id
            kwargs['dispositivo_id'] = dispositivo_id

            if form.is_valid():
                vd = form.save(commit=False)
                vd.save()
                self.kwargs['pk'] = vd.pk
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        except Exception as e:
            print(e)
        return HttpResponse("error post")


class VideEditView(VideMixin, UpdateView):
    model = Vide
    template_name = 'compilacao/ajax_form.html'
    form_class = forms.VideForm


class VideDeleteView(VideMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        vd = Vide.objects.get(pk=self.kwargs['pk'])
        vd.delete()
        return HttpResponseRedirect(self.get_success_url())


class DispositivoSearchFragmentFormView(ListView):
    template_name = 'compilacao/dispositivo_search_fragment_form.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(
            DispositivoSearchFragmentFormView,
            self).dispatch(*args, **kwargs)

    def get_queryset(self):
        try:
            busca = ''

            if 'busca' in self.request.GET:
                busca = self.request.GET['busca']

            q = Q(nivel__gt=0)
            busca = busca.split(' ')
            n = 10

            for item in busca:

                if not item:
                    continue

                if q:
                    q = q & (Q(dispositivo_pai__rotulo__icontains=item) |
                             Q(rotulo__icontains=item) |
                             Q(texto__icontains=item) |
                             Q(texto_atualizador__icontains=item))
                    n = 50
                else:
                    q = (Q(dispositivo_pai__rotulo__icontains=item) |
                         Q(rotulo__icontains=item) |
                         Q(texto__icontains=item) |
                         Q(texto_atualizador__icontains=item))
                    n = 50

            if 'tipo_ta' in self.request.GET:
                tipo_ta = self.request.GET['tipo_ta']
                if tipo_ta:
                    q = q & Q(ta__tipo_ta_id=tipo_ta)
                    n = 50

            if 'num_ta' in self.request.GET:
                num_ta = self.request.GET['num_ta']
                if num_ta:
                    q = q & Q(ta__numero=num_ta)
                    n = 50

            if 'ano_ta' in self.request.GET:
                ano_ta = self.request.GET['ano_ta']
                if ano_ta:
                    q = q & Q(ta__ano=ano_ta)
                    n = 50

            if 'initial_ref' in self.request.GET:
                initial_ref = self.request.GET['initial_ref']
                if initial_ref:
                    q = q & Q(pk=initial_ref)
                    n = 50

            return Dispositivo.objects.filter(q)[:n]

        except Exception as e:
            print(e)
