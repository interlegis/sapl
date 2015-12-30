from collections import OrderedDict
from datetime import datetime, timedelta
import sys

from braces.views import FormMessagesMixin
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout.containers import Fieldset
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.signing import Signer
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.forms.models import ModelForm
from django.http.response import (HttpResponse, HttpResponseRedirect,
                                  JsonResponse)
from django.shortcuts import get_object_or_404, redirect
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from compilacao import utils
from compilacao.forms import TaForm, NotaForm, VideForm
from compilacao.models import (Dispositivo, Nota,
                               PerfilEstruturalTextoArticulado,
                               TextoArticulado, TipoDispositivo, TipoNota,
                               TipoTextoArticulado, Vide, TipoVide,
                               TipoPublicacao, VeiculoPublicacao,
                               PARTICIPACAO_SOCIAL_CHOICES)
from compilacao.utils import build_crud, to_row, FormLayout


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

tipo_nota_crud = build_crud(
    TipoNota, 'tipo_nota', [

        [_('Tipo da Nota'),
         [('sigla', 2), ('nome', 10)],
         [('modelo', 12)]],
    ])

tipo_vide_crud = build_crud(
    TipoVide, 'tipo_vide', [

        [_('Tipo de Vide'),
         [('sigla', 2), ('nome', 10)]],
    ])

tipo_publicacao_crud = build_crud(
    TipoPublicacao, 'tipo_publicacao', [

        [_('Tipo de Publicação'),
         [('sigla', 2), ('nome', 10)]],
    ])


veiculo_publicacao_crud = build_crud(
    VeiculoPublicacao, 'veiculo_publicacao', [

        [_('Veículo de Publicação'),
         [('sigla', 2), ('nome', 10)]],
    ])


class IntegracaoTaView(TemplateView):

    def get(self, *args, **kwargs):
        item = get_object_or_404(self.model, pk=kwargs['pk'])
        related_object_type = ContentType.objects.get_for_model(item)

        ta = TextoArticulado.objects.filter(
            object_id=item.pk,
            content_type=related_object_type)

        if not ta.exists():
            ta = TextoArticulado()
            tipo_ta = TipoTextoArticulado.objects.filter(
                model=item.__class__.__name__.lower())[:1]
            if tipo_ta.exists():
                ta.tipo_ta = tipo_ta[0]
            ta.content_object = item
        else:
            ta = ta[0]

        if hasattr(item, 'ementa') and item.ementa:
            ta.ementa = item.ementa
        else:
            ta.ementa = 'Integração com %s sem ementa.' % item

        if hasattr(item, 'observacao') and item.observacao:
            ta.observacao = item.observacao
        else:
            ta.observacao = 'Integração com %s sem observacao.' % item

        if hasattr(item, 'numero') and item.numero:
            ta.numero = item.numero
        else:
            ta.numero = int('%s%s%s' % (
                int(datetime.now().year),
                int(datetime.now().month),
                int(datetime.now().day)))

        if hasattr(item, 'ano') and item.ano:
            ta.ano = item.ano
        else:
            ta.ano = datetime.now().year

        if hasattr(item, 'data_apresentacao'):
            ta.data = item.data_apresentacao
        elif hasattr(item, 'data'):
            ta.data = item.data
        else:
            ta.data = datetime.now()

        ta.save()

        return redirect(to=reverse_lazy('ta_text', kwargs={'ta_id': ta.pk}))

    class Meta:
        abstract = True


def get_integrations_view_names():
    result = []
    modules = sys.modules
    for key, value in modules.items():
        if key.endswith('.views'):
            for v in value.__dict__.values():
                if hasattr(v, '__bases__'):
                    for base in v.__bases__:
                        if base == IntegracaoTaView:
                            result.append(v)
    return result


def choice_extenal_views():
    integrations_view_names = get_integrations_view_names()
    result = []
    for item in integrations_view_names:
        ct = ContentType.objects.filter(
            model=item.model.__name__.lower(),
            app_label=item.model._meta.app_label)
        if ct.exists():
            result.append((
                ct[0].pk,
                item.model._meta.verbose_name_plural))
    return result


class TipoTaForm(ModelForm):
    sigla = forms.CharField(label='Sigla')
    descricao = forms.CharField(label='Descrição')

    participacao_social = forms.NullBooleanField(
        label=_('Participação Social'),
        widget=forms.Select(choices=PARTICIPACAO_SOCIAL_CHOICES),
        required=False)

    class Meta:
        model = TipoTextoArticulado
        fields = ['sigla',
                  'descricao',
                  'model',
                  'participacao_social',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('sigla', 2),
            ('descricao', 4),
            ('model', 3),
            ('participacao_social', 3),
        ])

        self.helper = FormHelper()
        self.helper.layout = FormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, css_class="large-12"))
        super(TipoTaForm, self).__init__(*args, **kwargs)


class TipoTaListView(ListView):
    model = TipoTextoArticulado
    paginate_by = 10
    verbose_name = model._meta.verbose_name
    title = model._meta.verbose_name_plural
    create_url = reverse_lazy('tipo_ta_create')


class TipoTaCreateView(FormMessagesMixin, CreateView):
    model = TipoTextoArticulado
    form_class = TipoTaForm
    template_name = "compilacao/form.html"
    form_valid_message = _('Registro criado com sucesso!')
    form_invalid_message = _('O registro não foi criado.')

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        form.fields['model'] = forms.ChoiceField(
            choices=choice_extenal_views(),
            label='Associação', required=False)

        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('tipo_ta_detail', kwargs={'pk': self.object.id})


class TipoTaDetailView(DetailView):
    model = TipoTextoArticulado

    @property
    def title(self):
        return self.get_object()


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
        if self.get_object().content_object:
            return _(
                'Metadados para o Texto Articulado da %s - %s') % (
                self.get_object().content_object._meta.verbose_name_plural,
                self.get_object().content_object)
        else:
            return self.get_object()


class TaCreateView(FormMessagesMixin, CreateView):
    model = TextoArticulado
    form_class = TaForm
    template_name = "compilacao/form.html"
    form_valid_message = _('Registro criado com sucesso!')
    form_invalid_message = _('O registro não foi criado.')

    def get_success_url(self):
        return reverse_lazy('ta_detail', kwargs={'pk': self.object.id})


class TaUpdateView(UpdateView):
    model = TextoArticulado
    form_class = TaForm
    template_name = "compilacao/form.html"

    @property
    def title(self):
        return self.get_object()

    def get_success_url(self):
        return reverse_lazy('ta_detail', kwargs={'pk': self.kwargs['pk']})

    @property
    def cancel_url(self):
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

    def get(self, request, *args, **kwargs):
        ta = TextoArticulado.objects.get(pk=self.kwargs['ta_id'])
        self.title = ta
        if ta.content_object:
            item = ta.content_object
            self.title = item
            if hasattr(item, 'ementa') and item.ementa:
                ta.ementa = item.ementa
            else:
                ta.ementa = 'Integração com %s sem ementa.' % item

            if hasattr(item, 'observacao') and item.observacao:
                ta.observacao = item.observacao
            else:
                ta.observacao = 'Integração com %s sem observacao.' % item

            if hasattr(item, 'numero') and item.numero:
                ta.numero = item.numero
            else:
                ta.numero = int('%s%s%s' % (
                    int(datetime.now().year),
                    int(datetime.now().month),
                    int(datetime.now().day)))

            if hasattr(item, 'ano') and item.ano:
                ta.ano = item.ano
            else:
                ta.ano = datetime.now().year

            if hasattr(item, 'data_apresentacao'):
                ta.data = item.data_apresentacao
            elif hasattr(item, 'data'):
                ta.data = item.data
            else:
                ta.data = datetime.now()
            ta.save()

        return super(TextView, self).get(request, *args, **kwargs)

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


class DispositivoEditView(TextEditView):
    template_name = 'compilacao/text_edit_bloco.html'

    def post(self, request, *args, **kwargs):

        d = Dispositivo.objects.get(
            pk=self.kwargs['dispositivo_id'])

        texto = request.POST['texto']

        if d.texto != '':
            d.texto = texto
            d.save()
            return self.get(request, *args, **kwargs)
        d.texto = texto.strip()
        d.save()

        if texto != '':
            dnext = Dispositivo.objects.filter(
                ta_id=d.ta_id,
                ordem__gt=d.ordem,
                texto='',
                tipo_dispositivo__dispositivo_de_articulacao=False)[:1]

            if not dnext.exists():
                dnext = []
                dnext[0] = d
            else:

                if dnext[0].nivel > d.nivel:
                    pais = [d.pk, ]
                else:
                    if dnext[0].dispositivo_pai_id == d.dispositivo_pai_id:
                        pais = [dnext[0].dispositivo_pai_id, ]
                    else:
                        pais = [
                            dnext[0].dispositivo_pai_id,
                            d.dispositivo_pai_id]
            data = {'pk': dnext[0].pk, 'pai': pais}
        else:
            data = {'pk': d.pk, 'pai': [d.pk, ]}

        return JsonResponse(data, safe=False)

    def get_queryset_perfil_estrutural(self):
        perfis = PerfilEstruturalTextoArticulado.objects.all()
        return perfis

    def get(self, request, *args, **kwargs):

        try:
            if 'perfil_pk' in request.GET:
                self.set_perfil_in_session(
                    request, request.GET['perfil_pk'])
            elif 'perfil_estrutural' not in request.session:
                self.set_perfil_in_session(request=request)

            self.object_list = self.get_queryset()

            self.perfil_estrutural_list = self.get_queryset_perfil_estrutural()

            context = self.get_context_data(
                object_list=self.object_list,
                perfil_estrutural_list=self.perfil_estrutural_list
            )
        except Exception as e:
            print(e)

        return self.render_to_response(context)

    def get_queryset(self):
        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1

        try:
            self.pk_edit = int(self.request.GET['edit'])
        except:
            self.pk_edit = 0
        self.pk_view = int(self.kwargs['dispositivo_id'])

        try:
            if self.pk_edit == self.pk_view:
                bloco = Dispositivo.objects.get(
                    pk=self.kwargs['dispositivo_id'])
            else:
                bloco = Dispositivo.objects.get(
                    pk=self.kwargs['dispositivo_id'])
        except Dispositivo.DoesNotExist:
            return []

        self.flag_nivel_old = bloco.nivel - 1
        self.flag_nivel_ini = bloco.nivel

        if self.pk_edit == self.pk_view:
            return [bloco, ]

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

    def select_provaveis_inserts(self, request=None):

        try:

            if request and 'perfil_estrutural' not in request.session:
                self.set_perfil_in_session(request)

            perfil_pk = request.session['perfil_estrutural']

            # Não salvar d_base
            if self.pk_edit == 0:
                base = Dispositivo.objects.get(pk=self.pk_view)
            else:
                base = Dispositivo.objects.get(pk=self.pk_edit)

            prox_possivel = Dispositivo.objects.filter(
                ordem__gt=base.ordem,
                nivel__lte=base.nivel,
                ta_id=base.ta_id)[:1]

            if prox_possivel.exists():
                prox_possivel = prox_possivel[0]
            else:
                prox_possivel = None

            result = [{'tipo_insert': 'Inserir Depois',
                       'icone': '&#8631;&nbsp;',
                       'action': 'add_next',
                       'itens': []},
                      {'tipo_insert': 'Inserir Dentro',
                       'icone': '&#8690;&nbsp;',
                       'action': 'add_in',
                       'itens': []},
                      {'tipo_insert': 'Inserir Antes',
                       'icone': '&#8630;&nbsp;',
                       'action': 'add_prior',
                       'itens': []}
                      ]

            # Possíveis inserções sequenciais já existentes
            parents = base.get_parents()
            parents.insert(0, base)
            nivel = sys.maxsize
            for dp in parents:

                if dp.nivel >= nivel:
                    continue

                if dp.is_relative_auto_insert(perfil_pk):
                    continue

                if prox_possivel and \
                    dp.tipo_dispositivo != base.tipo_dispositivo and\
                    dp.nivel < prox_possivel.nivel and\
                    not prox_possivel.tipo_dispositivo.permitido_inserir_in(
                        dp.tipo_dispositivo,
                        perfil_pk=perfil_pk):

                    if dp.tipo_dispositivo != prox_possivel.tipo_dispositivo:
                        continue

                nivel = dp.nivel

                # um do mesmo para inserção antes
                if dp == base:
                    result[2]['itens'].append({
                        'class_css': dp.tipo_dispositivo.class_css,
                        'tipo_pk': dp.tipo_dispositivo.pk,
                        'variacao': 0,
                        'provavel': '%s (%s)' % (
                            dp.rotulo_padrao(local_insert=1),
                            dp.tipo_dispositivo.nome,),
                        'dispositivo_base': base.pk})

                if dp.dispositivo_pai:
                    flag_pv = dp.tipo_dispositivo.permitido_variacao(
                        dp.dispositivo_pai.tipo_dispositivo,
                        perfil_pk=perfil_pk)
                else:
                    flag_pv = False

                r = []
                flag_direcao = 1
                flag_variacao = 0
                while True:
                    if dp.dispositivo0 == 0:
                        local_insert = 1
                    else:
                        local_insert = 0

                    rt = dp.transform_in_next(flag_direcao)
                    if not rt[0]:
                        break
                    flag_variacao += rt[1]
                    r.append({'class_css': dp.tipo_dispositivo.class_css,
                              'tipo_pk': dp.tipo_dispositivo.pk,
                              'variacao': flag_variacao,
                              'provavel': '%s (%s)' % (
                                  dp.rotulo_padrao(local_insert),
                                  dp.tipo_dispositivo.nome,),
                              'dispositivo_base': base.pk})

                    flag_direcao = -1

                r.reverse()

                if not flag_pv:
                    r = [r[0], ]

                if len(r) > 0 and dp.tipo_dispositivo.formato_variacao0 == \
                        TipoDispositivo.FNCN:
                    r = [r[0], ]

                if dp.tipo_dispositivo == base.tipo_dispositivo:
                    result[0]['itens'] += r
                else:
                    result[0]['itens'] += r
                    result[2]['itens'] += r

                if nivel == 0:
                    break

            # tipo do dispositivo base
            tipb = base.tipo_dispositivo

            for paradentro in [1, 0]:
                if paradentro:
                    # Outros Tipos de Dispositivos PARA DENTRO
                    otds = TipoDispositivo.objects.order_by(
                        '-contagem_continua', 'id').all()
                else:
                    # Outros Tipos de Dispositivos PARA FORA
                    classes_ja_inseridas = []
                    for c in result[0]['itens']:
                        if c['class_css'] not in classes_ja_inseridas:
                            classes_ja_inseridas.append(c['class_css'])
                    for c in result[1]['itens']:
                        if c['class_css'] not in classes_ja_inseridas:
                            classes_ja_inseridas.append(c['class_css'])
                    otds = TipoDispositivo.objects.order_by(
                        '-contagem_continua', 'id').all().exclude(
                            class_css__in=classes_ja_inseridas)

                for td in otds:

                    if paradentro and not td.permitido_inserir_in(
                        tipb,
                        include_relative_autos=False,
                            perfil_pk=perfil_pk):
                        continue

                    base.tipo_dispositivo = td

                    if not paradentro:

                        flag_insercao = False
                        for possivelpai in parents:
                            if td.permitido_inserir_in(
                                possivelpai.tipo_dispositivo,
                                include_relative_autos=False,
                                    perfil_pk=perfil_pk):
                                flag_insercao = True
                                break

                        if not flag_insercao:
                            continue

                        if possivelpai.is_relative_auto_insert(perfil_pk):
                            continue

                        if prox_possivel:
                            if prox_possivel.nivel == base.nivel:
                                if prox_possivel.tipo_dispositivo != td and\
                                    not prox_possivel.tipo_dispositivo.\
                                        permitido_inserir_in(
                                            td, perfil_pk=perfil_pk):
                                    continue
                            else:
                                if possivelpai.tipo_dispositivo != \
                                        prox_possivel.tipo_dispositivo and\
                                        not prox_possivel.tipo_dispositivo.\
                                        permitido_inserir_in(
                                            possivelpai.tipo_dispositivo,
                                            perfil_pk=perfil_pk) and \
                                        possivelpai.nivel < \
                                        prox_possivel.nivel:
                                    continue
                        base.dispositivo_pai = possivelpai
                        Dispositivo.set_numero_for_add_in(
                            possivelpai, base, td)
                    else:
                        Dispositivo.set_numero_for_add_in(base, base, td)

                    r = [{'class_css': td.class_css,
                          'tipo_pk': td.pk,
                          'variacao': 0,
                          'provavel': '%s (%s)' % (
                              base.rotulo_padrao(1, paradentro),
                              td.nome,),
                          'dispositivo_base': base.pk}]

                    if paradentro == 1:
                        """if (tipb.class_css == 'caput' and
                                td.class_css == 'paragrafo'):
                            result[0]['itens'].insert(0, r[0])
                        else:"""
                        result[1]['itens'] += r
                    else:
                        result[2]['itens'] += r
                        result[0]['itens'] += r

            # if len(result[0]['itens']) < len(result[1]['itens']):
            #    r = result[0]
            #    result.remove(result[0])
            #    result.insert(1, r)

            # remover temporariamente a opção inserir antes
            # confirmar falta de necessidade
            if len(result) > 2:
                result.pop()

        except Exception as e:
            print(e)

        return result


class ActionsEditMixin(object):

    def render_to_json_response(self, context, **response_kwargs):

        action = getattr(self, context['action'])
        return JsonResponse(action(context), safe=False)

    def delete_item_dispositivo(self, context):
        return self.delete_bloco_dispositivo(context)

    def delete_bloco_dispositivo(self, context):
        base = Dispositivo.objects.get(pk=context['dispositivo_id'])

        base_anterior = Dispositivo.objects.order_by('-ordem').filter(
            ta_id=base.ta_id,
            ordem__lt=base.ordem
        )[:1]
        base.delete()

        if base_anterior.exists():
            if base_anterior[0].dispositivo_pai_id:
                data = {'pk': base_anterior[0].pk, 'pai': [
                    base_anterior[0].dispositivo_pai_id, ]}
            else:
                data = {'pk': base_anterior[0].pk, 'pai': [-1, ]}
            return data
        else:
            return {}

    def add_prior(self, context):
        return {}

    def add_in(self, context):
        return self.add_next(context, local_add='add_in')

    def add_next(self, context, local_add='add_next'):
        try:
            base = Dispositivo.objects.get(pk=context['dispositivo_id'])
            tipo = TipoDispositivo.objects.get(pk=context['tipo_pk'])
            variacao = int(context['variacao'])
            parents = [base, ] + base.get_parents()

            tipos_dp_auto_insert = tipo.filhos_permitidos.filter(
                filho_de_insercao_automatica=True,
                perfil_id=context['perfil_pk'])

            count_auto_insert = 0
            for tipoauto in tipos_dp_auto_insert:
                qtdp = tipoauto.quantidade_permitida
                if qtdp >= 0:
                    qtdp -= Dispositivo.objects.filter(
                        ta_id=base.ta_id,
                        tipo_dispositivo_id=tipoauto.filho_permitido.pk
                    ).count()
                    if qtdp > 0:
                        count_auto_insert += 1
                else:
                    count_auto_insert += 1

            dp_irmao = None
            dp_pai = None
            for dp in parents:
                if dp.tipo_dispositivo == tipo:
                    dp_irmao = dp
                    break
                if tipo.permitido_inserir_in(
                        dp.tipo_dispositivo,
                        perfil_pk=context['perfil_pk']):
                    dp_pai = dp
                    break
                dp_pai = dp

            if dp_irmao is not None:
                dp = Dispositivo.new_instance_based_on(dp_irmao, tipo)
                dp.transform_in_next(variacao)
            else:
                # Inserção sem precedente
                dp = Dispositivo.new_instance_based_on(dp_pai, tipo)
                dp.dispositivo_pai = dp_pai
                dp.nivel += 1

                if tipo.contagem_continua:
                    ultimo_irmao = Dispositivo.objects.order_by(
                        '-ordem').filter(
                        ordem__lte=base.ordem,
                        tipo_dispositivo_id=tipo.pk,
                        ta_id=base.ta_id)[:1]

                    if not ultimo_irmao.exists():
                        dp.set_numero_completo([1, 0, 0, 0, 0, 0, ])
                    else:
                        ultimo_irmao = ultimo_irmao[0]
                        dp.set_numero_completo(
                            ultimo_irmao.get_numero_completo())
                        dp.transform_in_next()
                else:
                    if ';' in tipo.rotulo_prefixo_texto:
                        dp.set_numero_completo([0, 0, 0, 0, 0, 0, ])
                    else:
                        dp.set_numero_completo([1, 0, 0, 0, 0, 0, ])

            # verificar se existe restrição de quantidade de itens
            if dp.dispositivo_pai:
                pp = dp.tipo_dispositivo.possiveis_pais.filter(
                    pai_id=dp.dispositivo_pai.tipo_dispositivo_id,
                    perfil_id=context['perfil_pk'])

                if pp.exists() and pp[0].quantidade_permitida >= 0:
                    qtd_existente = Dispositivo.objects.filter(
                        ta_id=dp.ta_id,
                        tipo_dispositivo_id=dp.tipo_dispositivo_id).count()

                    if qtd_existente >= pp[0].quantidade_permitida:
                        return {'pk': base.pk,
                                'pai': [base.dispositivo_pai.pk, ],
                                'alert': str(_('Limite de inserções de '
                                               'dispositivos deste tipo '
                                               'foi excedido.'))
                                }

            ordem = base.criar_espaco(
                espaco_a_criar=1 + count_auto_insert, local=local_add)

            dp.rotulo = dp.rotulo_padrao()
            dp.ordem = ordem
            dp.incrementar_irmaos(variacao, [local_add, ])

            dp.clean()
            dp.save()

            dp_auto_insert = None

            # Inserção automática
            if count_auto_insert:
                dp_pk = dp.pk
                dp.nivel += 1
                for tipoauto in tipos_dp_auto_insert:
                    dp.dispositivo_pai_id = dp_pk
                    dp.pk = None
                    dp.tipo_dispositivo = tipoauto.filho_permitido
                    if ';' in dp.tipo_dispositivo.rotulo_prefixo_texto:
                        dp.set_numero_completo([0, 0, 0, 0, 0, 0, ])
                    else:
                        dp.set_numero_completo([1, 0, 0, 0, 0, 0, ])
                    dp.rotulo = dp.rotulo_padrao()
                    dp.texto = ''
                    dp.ordem = dp.ordem + Dispositivo.INTERVALO_ORDEM
                    dp.clean()
                    dp.save()
                    dp_auto_insert = dp
                dp = Dispositivo.objects.get(pk=dp_pk)

            ''' Reenquadrar todos os dispositivos que possuem pai
            antes da inserção atual e que são inferiores a dp,
            redirecionando para o novo pai'''

            nivel = sys.maxsize
            flag_niveis = False

            if not dp.tipo_dispositivo.dispositivo_de_alteracao:
                possiveis_filhos = Dispositivo.objects.filter(
                    ordem__gt=dp.ordem,
                    ta_id=dp.ta_id)

                for filho in possiveis_filhos:

                    if filho.nivel > nivel:
                        continue

                    if filho.dispositivo_pai.ordem >= dp.ordem:
                        continue

                    nivel = filho.nivel

                    if not filho.tipo_dispositivo.permitido_inserir_in(
                        dp.tipo_dispositivo,
                            perfil_pk=context['perfil_pk']):
                        continue

                    filho.dispositivo_pai = dp
                    filho.clean()
                    filho.save()
                    flag_niveis = True

            if flag_niveis:
                dp.organizar_niveis()

            numtipos = {}

            ''' Renumerar filhos imediatos que
            não possuam contagem continua'''

            if flag_niveis:
                filhos = Dispositivo.objects.filter(
                    dispositivo_pai_id=dp.pk)

                for filho in filhos:

                    if filho.tipo_dispositivo.contagem_continua:
                        continue

                    if filho.tipo_dispositivo.class_css in numtipos:
                        if filho.dispositivo_substituido is None:
                            numtipos[filho.tipo_dispositivo.class_css] += 1
                    else:
                        t = filho.tipo_dispositivo
                        prefixo = t.rotulo_prefixo_texto.split(';')
                        if len(prefixo) > 1:
                            count_irmaos_m_tipo = Dispositivo.objects.filter(
                                ~Q(pk=filho.pk),
                                tipo_dispositivo=t,
                                dispositivo_pai=filho.dispositivo_pai)[:1]

                            if count_irmaos_m_tipo.exists():
                                numtipos[filho.tipo_dispositivo.class_css] = 1
                            else:
                                numtipos[filho.tipo_dispositivo.class_css] = 0
                        else:
                            numtipos[filho.tipo_dispositivo.class_css] = 1

                    filho.dispositivo0 = numtipos[
                        filho.tipo_dispositivo.class_css]

                    filho.rotulo = filho.rotulo_padrao()
                    filho.clean()
                    filho.save()

            ''' Renumerar dispositivos de
            contagem continua, caso a inserção seja uma articulação'''

            numtipos = {}
            if dp.nivel == 0:

                proxima_articulacao = Dispositivo.objects.filter(
                    ordem__gt=dp.ordem,
                    nivel=0,
                    ta_id=dp.ta_id)[:1]

                if not proxima_articulacao.exists():
                    filhos_continuos = list(Dispositivo.objects.filter(
                        ordem__gt=dp.ordem,
                        ta_id=dp.ta_id,
                        tipo_dispositivo__contagem_continua=True))
                else:
                    filhos_continuos = list(Dispositivo.objects.filter(
                        Q(ordem__gt=dp.ordem) &
                        Q(ordem__lt=proxima_articulacao[0].ordem),
                        ta_id=dp.ta_id,
                        tipo_dispositivo__contagem_continua=True))

                for filho in filhos_continuos:

                    if filho.tipo_dispositivo.class_css in numtipos:
                        if filho.dispositivo_substituido is None:
                            numtipos[filho.tipo_dispositivo.class_css] += 1
                    else:
                        t = filho.tipo_dispositivo
                        prefixo = t.rotulo_prefixo_texto.split(';')
                        if len(prefixo) > 1:
                            count_irmaos_m_tipo = Dispositivo.objects.filter(
                                ~Q(pk=filho.pk),
                                tipo_dispositivo=t,
                                dispositivo_pai=filho.dispositivo_pai)[:1]

                            if count_irmaos_m_tipo.exists():
                                numtipos[filho.tipo_dispositivo.class_css] = 1
                            else:
                                numtipos[filho.tipo_dispositivo.class_css] = 0
                        else:
                            numtipos[filho.tipo_dispositivo.class_css] = 1

                    filho.dispositivo0 = numtipos[
                        filho.tipo_dispositivo.class_css]

                    filho.rotulo = filho.rotulo_padrao()
                    filho.clean()
                    filho.save()

        except Exception as e:
            print(e)

        if dp_auto_insert is None:
            data = self.get_json_for_refresh(dp)
        else:
            data = self.get_json_for_refresh(dp=dp, dpauto=dp_auto_insert)

        return data

    def get_json_for_refresh(self, dp, dpauto=None):

        if dp.tipo_dispositivo.contagem_continua:
            pais = []
            if dp.dispositivo_pai is None:
                data = {'pk': dp.pk, 'pai': [-1, ]}
            else:
                pkfilho = dp.pk
                dp = dp.dispositivo_pai

                proxima_articulacao = dp.get_proximo_nivel_zero()

                if proxima_articulacao is not None:
                    parents = Dispositivo.objects.filter(
                        ta_id=dp.ta_id,
                        ordem__gte=dp.ordem,
                        ordem__lt=proxima_articulacao.ordem,
                        nivel__lte=dp.nivel)
                else:
                    parents = Dispositivo.objects.filter(
                        ta_id=dp.ta_id,
                        ordem__gte=dp.ordem,
                        nivel__lte=dp.nivel)

                nivel = sys.maxsize
                for p in parents:
                    if p.nivel > nivel:
                        continue
                    pais.append(p.pk)
                    nivel = p.nivel
                data = {
                    'pk': pkfilho if not dpauto else dpauto.pk, 'pai': pais}
        else:
            data = {'pk': dp.pk if not dpauto else dpauto.pk, 'pai': [
                dp.dispositivo_pai.pk, ]}

        return data


class ActionsEditView(ActionsEditMixin, TemplateView):

    def render_to_response(self, context, **response_kwargs):
        context['action'] = self.request.GET['action']

        if 'tipo_pk' in self.request.GET:
            context['tipo_pk'] = self.request.GET['tipo_pk']

        if 'variacao' in self.request.GET:
            context['variacao'] = self.request.GET['variacao']

        if 'perfil_estrutural' in self.request.session:
            context['perfil_pk'] = self.request.session['perfil_estrutural']

        return self.render_to_json_response(context, **response_kwargs)


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
    form_class = NotaForm

    def get(self, request, *args, **kwargs):
        flag_action, modelo_nota = self.get_modelo_nota(request)
        if flag_action:
            return HttpResponse(modelo_nota)

        return super(NotasCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            ta_id = kwargs.pop('ta_id')
            dispositivo_id = kwargs.pop('dispositivo_id')
            form = NotaForm(request.POST, request.FILES, **kwargs)
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
    form_class = NotaForm

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
    form_class = VideForm

    def post_old(self, request, *args, **kwargs):
        try:
            self.object = None
            ta_id = kwargs.pop('ta_id')
            dispositivo_id = kwargs.pop('dispositivo_id')
            form = VideForm(request.POST, request.FILES, **kwargs)
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
    form_class = VideForm


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
