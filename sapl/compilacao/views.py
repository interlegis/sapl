import logging
import sys
from collections import OrderedDict
from datetime import timedelta

from braces.views import FormMessagesMixin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.signing import Signer
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import connection, transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http.response import (HttpResponse, HttpResponseRedirect,
                                  JsonResponse)
from django.shortcuts import get_object_or_404, redirect
from django.utils.dateparse import parse_date
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, DeleteView, FormView,
                                       UpdateView)
from django.views.generic.list import ListView

from sapl.compilacao.apps import AppConfig
from sapl.compilacao.forms import (DispositivoDefinidorVigenciaForm,
                                   DispositivoEdicaoAlteracaoForm,
                                   DispositivoEdicaoBasicaForm,
                                   DispositivoEdicaoVigenciaForm,
                                   DispositivoRegistroAlteracaoForm,
                                   DispositivoRegistroInclusaoForm,
                                   DispositivoRegistroRevogacaoForm,
                                   DispositivoSearchModalForm, NotaForm,
                                   PublicacaoForm, TaForm,
                                   TextNotificacoesForm, TipoTaForm, VideForm)
from sapl.compilacao.models import (STATUS_TA_EDITION, STATUS_TA_PRIVATE,
                                    STATUS_TA_PUBLIC, Dispositivo, Nota,
                                    PerfilEstruturalTextoArticulado,
                                    Publicacao, TextoArticulado,
                                    TipoDispositivo, TipoNota, TipoPublicacao,
                                    TipoTextoArticulado, TipoVide,
                                    VeiculoPublicacao, Vide)
from sapl.compilacao.utils import (DISPOSITIVO_SELECT_RELATED,
                                   DISPOSITIVO_SELECT_RELATED_EDIT,
                                   get_integrations_view_names)
from sapl.crud.base import Crud, CrudAux, CrudListView, make_pagination
from sapl.settings import BASE_DIR

TipoNotaCrud = CrudAux.build(TipoNota, 'tipo_nota')
TipoVideCrud = CrudAux.build(TipoVide, 'tipo_vide')
TipoPublicacaoCrud = CrudAux.build(TipoPublicacao, 'tipo_publicacao')
VeiculoPublicacaoCrud = CrudAux.build(VeiculoPublicacao, 'veiculo_publicacao')
TipoDispositivoCrud = CrudAux.build(
    TipoDispositivo, 'tipo_dispositivo')

logger = logging.getLogger(BASE_DIR.name)


def choice_models_in_extenal_views():
    integrations_view_names = get_integrations_view_names()
    result = [(None, '-------------'), ]
    for item in integrations_view_names:
        if hasattr(item, 'model') and hasattr(item, 'model_type_foreignkey'):
            ct = ContentType.objects.filter(
                model=item.model.__name__.lower(),
                app_label=item.model._meta.app_label)
            if ct.exists():
                result.append((
                    ct[0].pk,
                    item.model._meta.verbose_name_plural))
    return result


def choice_model_type_foreignkey_in_extenal_views(id_tipo_ta=None):
    yield None, '-------------'

    if not id_tipo_ta:
        return

    tipo_ta = TipoTextoArticulado.objects.get(pk=id_tipo_ta)

    integrations_view_names = get_integrations_view_names()
    for item in integrations_view_names:
        if hasattr(item, 'model_type_foreignkey'):
            if (tipo_ta.content_type.model == item.model.__name__.lower() and
                    tipo_ta.content_type.app_label ==
                    item.model._meta.app_label):
                for i in item.model_type_foreignkey.objects.all():
                    yield i.pk, i


class IntegracaoTaView(TemplateView):

    def get_redirect_deactivated(self):
        messages.error(
            self.request,
            _('O modulo de Textos Articulados para %s está desativado.'
              ) % self.model._meta.verbose_name_plural)
        return redirect('/')

    def get(self, request,  *args, **kwargs):

        try:
            if settings.DEBUG or not TipoDispositivo.objects.exists():
                AppConfig.import_pattern()

                if hasattr(self, 'map_funcs'):
                    tipo_ta = TipoTextoArticulado.objects.get(
                        content_type=ContentType.objects.get_for_model(
                            self.model))

                    for key, value in self.map_funcs.items():
                        setattr(tipo_ta, key, value)
                    tipo_ta.save()

        except Exception as e:
            logger.error(
                string_concat(
                    _('Ocorreu erro na importação do arquivo base dos Tipos de'
                      'Dispositivos, entre outras informações iniciais.'),
                    str(e)))
            return self.get_redirect_deactivated()

        assert hasattr(self, 'map_fields'), _(
            """
                O mapa dos campos não foi definido. Ele deve seguir a estrutura
                de chaves abaixo:

                    map_fields = {
                        'data': 'data',
                        'ementa': 'ementa',
                        'observacao': 'observacao',
                        'numero': 'numero',
                        'ano': 'ano',
                    }

                Caso o model de integração não possua um dos campos,
                implemente, ou passe `None` para as chaves que são fixas.
            """)

        ta_values = getattr(self, 'ta_values', {})

        item = get_object_or_404(self.model, pk=kwargs['pk'])
        related_object_type = ContentType.objects.get_for_model(item)

        ta = TextoArticulado.objects.filter(
            object_id=item.pk,
            content_type=related_object_type)

        ta_exists = bool(ta.exists())
        if (ta_exists or
                (request.user.has_perm(
                    'compilacao.change_dispositivo_edicao_dinamica') and
                 ta_values.get('privacidade', STATUS_TA_EDITION
                               ) != STATUS_TA_PRIVATE) or
                (request.user.has_perm(
                    'compilacao.change_your_dispositivo_edicao_dinamica') and
                 ta_values.get('privacidade', STATUS_TA_EDITION
                               ) == STATUS_TA_PRIVATE)):
            """
            o texto articulado será criado/atualizado se:
                - texto articulado já foi criado.

                - não foi criado e o usuário possui permissão para criar
                  desde que o texto não seja um texto privado pois a permissão
                  para criar textos privados é diferente.

                - não foi criado e o usuário possui permissão para criar desde
                  que o texto seja privado e a permissão seja específica para
                  textos privados.
            """
            pass
        else:
            messages.info(request, _('%s não possui %s.') % (
                item, TextoArticulado._meta.verbose_name))
            return redirect('/message')

        ta = TextoArticulado.update_or_create(self, item)

        if not ta_exists:
            if ta.editable_only_by_owners and\
                    not self.request.user.is_anonymous():
                ta.owners.add(self.request.user)

        if not Dispositivo.objects.filter(ta_id=ta.pk).exists() and\
                ta.can_use_dynamic_editing(self.request.user):
            return redirect(to=reverse_lazy('sapl.compilacao:ta_text_edit',
                                            kwargs={'ta_id': ta.pk}))
        else:
            return redirect(to=reverse_lazy('sapl.compilacao:ta_text',
                                            kwargs={'ta_id': ta.pk}))

    class Meta:
        abstract = True


class CompMixin(PermissionRequiredMixin):
    permission_required = []

    def has_permission(self):
        perms = self.get_permission_required()
        # Torna a view pública se não possuir conteudo
        # no atributo permission_required
        return self.request.user.has_perms(perms) if len(perms) else True

    @property
    def ta(self):
        ta = TextoArticulado.objects.get(
            pk=self.kwargs.get('ta_id', self.kwargs.get('pk', 0)))
        return ta

    def get_context_data(self, **kwargs):
        context = super(CompMixin, self).get_context_data(**kwargs)

        if hasattr(self, 'model') and not hasattr(self, 'object'):
            context.update(
                {'title': self.model._meta.verbose_name_plural
                 if isinstance(self, ListView)
                    else self.model._meta.verbose_name})

        if isinstance(self, ListView):
            context['NO_ENTRIES_MSG'] = CrudListView.no_entries_msg
        return context

    def get_notificacoes(self, object_list=None, type_notificacoes=None):

        p = []

        def padd(r, type_notificacao, reverse_url=None, test=True, msg='',
                 kwargs=None, to_position=None):

            if not test:
                return

            r.contextual_class = type_notificacao
            if not kwargs:
                kwargs = {'ta_id': r.ta_id, 'pk': r.pk}
            if reverse_url:
                p.append((type_notificacao, msg,
                          reverse_lazy(reverse_url, kwargs=kwargs),
                          to_position))
            else:
                p.append((type_notificacao, msg, None, to_position))

        def success(r):
            type_notificacao = 'success'
            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.inconstitucionalidade,
                 _('Declarado Inconstitucional.'))

            padd(r, type_notificacao, 'sapl.compilacao:ta_text_edit',
                 r.ta_publicado and r.dispositivo_atualizador,
                 _('Dispositivo alterado em %s' % r.ta_publicado),
                 {'ta_id': r.ta_publicado_id}, r.dispositivo_atualizador_id)

        def info(r):
            type_notificacao = 'info'
            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.publicacao and
                 r.dispositivo_vigencia and
                 r.publicacao.data != r.dispositivo_vigencia.inicio_vigencia,
                 _('Data da publicação associada ao Dispositivo difere da data'
                   ' de inicio de vigência do Dispositivo de vigência.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.publicacao and r.publicacao.data != r.inicio_vigencia,
                 _('Data da publicação associada ao Dispositivo difere '
                   'da data de inicio de vigência.'))

            padd(r, type_notificacao, 'sapl.compilacao:dispositivo_edit',
                 r.rotulo != r.rotulo_padrao(local_insert=1),
                 _('Rótulo Diferente do Padrão'))

            padd(r, type_notificacao, 'sapl.compilacao:dispositivo_edit',
                 r.texto_atualizador and r.texto_atualizador != r.texto,
                 _('Texto do Dispositivo para o Documento '
                   'está diferente do texto para o Documento Alterador.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 r.texto_atualizador and r.texto_atualizador == r.texto,
                 _('Texto do Dispositivo no Documento Alterador '
                   'está igual ao Texto no Documento Original. '
                   'Não é necessário manter armazenado o texto no Documento '
                   'Alterador.'))

        def warning(r):
            type_notificacao = 'warning'
            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.dispositivo_vigencia and r.inicio_vigencia !=
                 r.dispositivo_vigencia.inicio_vigencia,
                 _('Data de início de Vigência difere da data início de '
                   'Vigência do Dispositivo de Vigência'))

            padd(r, type_notificacao, 'sapl.compilacao:ta_text',
                 r.inconstitucionalidade and not r.notas.exists(),
                 _('Dispositivo está definido como inconstitucional. É '
                   'aconcelhavel inserir uma Nota informando esta condição.'),
                 kwargs={'ta_id': r.ta_id},
                 to_position=r.pk)

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.inconstitucionalidade and not (
                     r.inicio_vigencia == r.fim_vigencia and
                     r.fim_vigencia == r.inicio_eficacia and
                     r.inicio_eficacia == r.fim_eficacia),
                 _('Dispositivo está definido como inconstitucional porém '
                   'existe diferença entre as datas início e fim de '
                   'vigência e eficácia.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.publicacao and
                 r.ta_publicado and r.ta_publicado != r.publicacao.ta,
                 _('A Publicação associada a este Dispositivo não é '
                   'uma publicação do Texto Articulado Alterador.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 not r.publicacao,
                 _('Dispositivo sem registro de publicação.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.texto and r.tipo_dispositivo.dispositivo_de_articulacao,
                 _('Dispositivos de Articulação não '
                   'deveriam armazenar texto.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 not r.texto and
                 not r.tipo_dispositivo.dispositivo_de_articulacao,
                 _('Dispositivo está sem texto.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 r.texto_atualizador and not r.ta_publicado,
                 _('Existe Texto Atualizador, porém este Dispositivo não '
                   'está associado a nenhum Documento Atualizador.'))

        def danger(r):
            type_notificacao = 'danger'
            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 not r.dispositivo_vigencia,
                 _('Dispositivo sem definição de Dispositivo de Vigência.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_vigencia',
                 r.inconstitucionalidade and
                 r.inicio_vigencia != r.fim_vigencia,
                 _('Dispositivo está definido como inconstitucional porém '
                   'existe período de vigência.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 r.ta_publicado and not r.dispositivo_atualizador,
                 _('Dispositivo está associado a um Texto Articulado '
                   'Atualizador mas, a nenhum Dispositivo Atualizador.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 not r.dispositivo_atualizador and
                 r.dispositivo_substituido,
                 _('Dispositivo está substituindo outro mas não foi informado '
                   'o Dispositivo Atualizador.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 r.dispositivo_substituido and
                 r.dispositivo_substituido.tipo_dispositivo !=
                 r.tipo_dispositivo,
                 _('Dispositivo está substituindo um Dispositivo '
                   'de outro tipo.'))

            padd(r, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 r.dispositivo_substituido and
                 r.dispositivo_substituido.ta != r.ta,
                 _('Dispositivo está substituindo um Dispositivo de outro '
                   'Texto Articulado.'))

            padd(r.dispositivo_substituido, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 r.dispositivo_substituido and
                 r.dispositivo_substituido.dispositivo_subsequente != r,
                 _('Dispositivo está substituindo um Dispositivo que não '
                   'possui este como seu Dispositivo Subsequente.'))

            padd(r.dispositivo_subsequente, type_notificacao,
                 'sapl.compilacao:dispositivo_edit_alteracao',
                 r.dispositivo_subsequente and
                 r.dispositivo_subsequente.dispositivo_substituido != r,
                 _('Dispositivo foi substituído por outro que não '
                   'possui este como seu Dispositivo Substituído.'))

        rr = []
        for r in object_list:
            p = []
            r.contextual_class = ""

            for f in type_notificacoes:
                if f != 'default':
                    locals()[f](r)

            r.notificacoes = p

            if p or 'default' in type_notificacoes:
                rr.append(r)

            if r.dispositivos_alterados_set.exists():
                rr += self.get_notificacoes(
                    r.dispositivos_alterados_set.all(), type_notificacoes)

        return rr


class TipoTaListView(CompMixin, ListView):
    model = TipoTextoArticulado
    paginate_by = 10
    verbose_name = model._meta.verbose_name
    permission_required = 'compilacao.list_tipotextoarticulado'

    @property
    def title(self):
        return self.model._meta.verbose_name_plural

    @property
    def create_url(self):
        return reverse_lazy('sapl.compilacao:tipo_ta_create')


class TipoTaCreateView(CompMixin, FormMessagesMixin, CreateView):
    model = TipoTextoArticulado
    form_class = TipoTaForm
    template_name = "crud/form.html"
    form_valid_message = _('Registro criado com sucesso!')
    form_invalid_message = _('O registro não foi criado.')
    permission_required = 'compilacao.add_tipotextoarticulado'

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        form.fields['content_type'] = forms.ChoiceField(
            choices=choice_models_in_extenal_views(),
            label=_('Modelo Integrado'), required=False)

        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:tipo_ta_detail',
                            kwargs={'pk': self.object.id})

    @property
    def cancel_url(self):
        return reverse_lazy('sapl.compilacao:tipo_ta_list')


class TipoTaDetailView(CompMixin, DetailView):
    model = TipoTextoArticulado
    permission_required = 'compilacao.detail_tipotextoarticulado'


class TipoTaUpdateView(CompMixin, UpdateView):
    model = TipoTextoArticulado
    form_class = TipoTaForm
    template_name = "crud/form.html"
    permission_required = 'compilacao.change_tipotextoarticulado'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        form.fields['content_type'] = forms.ChoiceField(
            choices=choice_models_in_extenal_views(),
            label=_('Modelo Integrado'), required=False)
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:tipo_ta_detail',
                            kwargs={'pk': self.kwargs['pk']})

    @property
    def cancel_url(self):
        return reverse_lazy('sapl.compilacao:tipo_ta_detail',
                            kwargs={'pk': self.kwargs['pk']})


class TipoTaDeleteView(CompMixin, DeleteView):
    model = TipoTextoArticulado
    template_name = "crud/confirm_delete.html"
    permission_required = 'compilacao.delete_tipotextoarticulado'

    @property
    def detail_url(self):
        return reverse_lazy('sapl.compilacao:tipo_ta_detail',
                            kwargs={'pk': self.kwargs['pk']})

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:tipo_ta_list')


class TaListView(CompMixin, ListView):
    model = TextoArticulado
    paginate_by = 10
    verbose_name = model._meta.verbose_name
    permission_required = 'compilacao.list_textoarticulado'

    @property
    def title(self):
        return self.model._meta.verbose_name_plural

    @property
    def create_url(self):
        return reverse_lazy('sapl.compilacao:ta_create')

    def get_context_data(self, **kwargs):
        context = super(TaListView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        return context

    def get_queryset(self):
        qs = ListView.get_queryset(self)

        qs = qs.exclude(
            ~Q(owners=self.request.user.id),
            privacidade=STATUS_TA_PRIVATE)

        return qs


class TaDetailView(CompMixin, DetailView):
    model = TextoArticulado

    def has_permission(self):
        self.object = self.ta
        if self.object.has_view_permission(self.request):
            return CompMixin.has_permission(self)
        else:
            return False

    @property
    def title(self):
        if self.get_object().content_object:
            return _(
                'Metadados para o Texto Articulado de %s\n'
                '<small>%s</small>') % (
                self.get_object().content_object._meta.verbose_name_plural,
                self.get_object().content_object)
        else:
            return self.get_object()


class TaCreateView(CompMixin, FormMessagesMixin, CreateView):
    model = TextoArticulado
    form_class = TaForm
    template_name = "crud/form.html"
    form_valid_message = _('Registro criado com sucesso!')
    form_invalid_message = _('O registro não foi criado.')
    permission_required = 'compilacao.add_tipotextoarticulado'

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:ta_detail',
                            kwargs={'pk': self.object.id})

    @property
    def cancel_url(self):
        return reverse_lazy('sapl.compilacao:ta_list')


class TaUpdateView(CompMixin, UpdateView):
    model = TextoArticulado
    form_class = TaForm
    template_name = "crud/form.html"
    permission_required = 'compilacao.change_textoarticulado'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        # if self.object and self.object.content_object:
        #    form.fields['tipo_ta'].required = False
        #    form.fields['tipo_ta'].widget.attrs['disabled'] = 'disabled'
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:ta_detail',
                            kwargs={'pk': self.kwargs['pk']})

    @property
    def cancel_url(self):
        return reverse_lazy('sapl.compilacao:ta_detail',
                            kwargs={'pk': self.kwargs['pk']})


class TaDeleteView(CompMixin, DeleteView):
    model = TextoArticulado
    template_name = "crud/confirm_delete.html"
    permission_required = 'compilacao.delete_textoarticulado'

    @property
    def detail_url(self):
        return reverse_lazy('sapl.compilacao:ta_detail',
                            kwargs={'pk': self.kwargs['pk']})

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:ta_list')


class DispositivoSuccessUrlMixin(CompMixin):

    def get_success_url(self):
        return reverse_lazy(
            'sapl.compilacao:dispositivo', kwargs={
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


class NotasCreateView(NotaMixin, CreateView):
    template_name = 'compilacao/ajax_form.html'
    form_class = NotaForm
    permission_required = 'compilacao.add_nota'

    def get(self, request, *args, **kwargs):
        flag_action, modelo_nota = self.get_modelo_nota(request)
        if flag_action:
            return HttpResponse(modelo_nota)

        return super(NotasCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
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
    permission_required = 'compilacao.change_nota'

    def get(self, request, *args, **kwargs):
        flag_action, modelo_nota = self.get_modelo_nota(request)
        if flag_action:
            return HttpResponse(modelo_nota)

        return super(NotasEditView, self).get(request, *args, **kwargs)


class NotasDeleteView(NotaMixin, TemplateView):

    permission_required = 'compilacao.delete_nota'

    def get(self, request, *args, **kwargs):
        nt = Nota.objects.get(pk=self.kwargs['pk'])
        nt.delete()
        return HttpResponseRedirect(self.get_success_url())


class VideMixin(DispositivoSuccessUrlMixin):

    def get_initial(self):
        dispositivo_base = get_object_or_404(
            Dispositivo, pk=self.kwargs.get('dispositivo_id'))
        initial = {'dispositivo_base': dispositivo_base, }

        if 'pk' in self.kwargs:
            initial['pk'] = self.kwargs.get('pk')

        return initial


class VideCreateView(VideMixin, CreateView):
    model = Vide
    template_name = 'compilacao/ajax_form.html'
    form_class = VideForm
    permission_required = 'compilacao.add_vide'

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))


class VideEditView(VideMixin, UpdateView):
    model = Vide
    template_name = 'compilacao/ajax_form.html'
    form_class = VideForm
    permission_required = 'compilacao.change_vide'


class VideDeleteView(VideMixin, TemplateView):
    permission_required = 'compilacao.delete_vide'

    def get(self, request, *args, **kwargs):
        vd = Vide.objects.get(pk=self.kwargs['pk'])
        vd.delete()
        return HttpResponseRedirect(self.get_success_url())


class PublicacaoMixin(CompMixin):

    def dispatch(self, request, *args, **kwargs):
        ta = self.ta
        if not ta.tipo_ta.publicacao_func:
            messages.error(request, _(
                'A funcionalidade de %s está desativada para %s.') % (
                TipoTextoArticulado._meta.get_field(
                    'publicacao_func').verbose_name,
                ta.tipo_ta.descricao))
            return redirect(reverse('sapl.compilacao:ta_text',
                                    kwargs={'ta_id': self.kwargs['ta_id']}))

        return PermissionRequiredMixin.dispatch(self, request, *args, **kwargs)


class PublicacaoListView(PublicacaoMixin, ListView):
    model = Publicacao
    verbose_name = model._meta.verbose_name
    permission_required = []

    @property
    def title(self):
        return _('%s <small>(%s)</small>' % (
            self.model._meta.verbose_name_plural,
            self.ta))

    @property
    def create_url(self):
        return reverse_lazy(
            'sapl.compilacao:ta_pub_create',
            kwargs={'ta_id': self.kwargs['ta_id']})

    def get_queryset(self):
        pubs = Publicacao.objects.filter(ta_id=self.kwargs['ta_id'])
        return pubs

    def get_context_data(self, **kwargs):
        context = super(PublicacaoListView, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['object'] = self.ta
        context['NO_ENTRIES_MSG'] = CrudListView.no_entries_msg
        return context


class PublicacaoCreateView(PublicacaoMixin, FormMessagesMixin, CreateView):
    model = Publicacao
    form_class = PublicacaoForm
    template_name = "crud/form.html"
    form_valid_message = _('Registro criado com sucesso!')
    form_invalid_message = _('O registro não foi criado.')
    permission_required = 'compilacao.add_publicacao'

    def get_success_url(self):
        return reverse_lazy(
            'sapl.compilacao:ta_pub_detail',
            kwargs={
                'pk': self.object.id,
                'ta_id': self.kwargs['ta_id']})

    @property
    def cancel_url(self):
        return reverse_lazy(
            'sapl.compilacao:ta_pub_list',
            kwargs={'ta_id': self.kwargs['ta_id']})

    def get_initial(self):
        return {'ta': self.kwargs['ta_id']}


class PublicacaoDetailView(PublicacaoMixin, DetailView):
    model = Publicacao
    permission_required = []

    @property
    def list_url(self):
        return reverse_lazy('sapl.compilacao:ta_pub_list',
                            kwargs={
                                'ta_id': self.kwargs['ta_id']})

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural


class PublicacaoUpdateView(PublicacaoMixin, UpdateView):
    model = Publicacao
    form_class = PublicacaoForm
    template_name = "crud/form.html"
    permission_required = 'compilacao.change_publicacao'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        # if self.object and self.object.content_object:
        #    form.fields['tipo_ta'].required = False
        #    form.fields['tipo_ta'].widget.attrs['disabled'] = 'disabled'
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:ta_pub_detail',
                            kwargs={
                                'pk': self.object.id,
                                'ta_id': self.kwargs['ta_id']})

    @property
    def cancel_url(self):
        return self.get_success_url()


class PublicacaoDeleteView(PublicacaoMixin, DeleteView):
    model = Publicacao
    template_name = "crud/confirm_delete.html"
    permission_required = 'compilacao.delete_publicacao'

    @property
    def detail_url(self):
        return reverse_lazy('sapl.compilacao:ta_pub_detail',
                            kwargs={
                                'pk': self.object.id,
                                'ta_id': self.kwargs['ta_id']})

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:ta_pub_list',
                            kwargs={'ta_id': self.kwargs['ta_id']})


class TextView(CompMixin, ListView):
    template_name = 'compilacao/text_list.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    itens_de_vigencia = {}

    inicio_vigencia = None
    fim_vigencia = None
    ta_vigencia = None

    def has_permission(self):
        self.object = self.ta
        return self.object.has_view_permission(self.request)

    def get(self, request, *args, **kwargs):
        if 'print' in request.GET:
            self.template_name = 'compilacao/text_list__print_version.html'
        return ListView.get(self, request, *args, **kwargs)

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
            if c.dispositivo_base_id not in context['cita']:
                context['cita'][c.dispositivo_base_id] = []
            context['cita'][c.dispositivo_base_id].append(c)

        citado = Vide.objects.filter(
            Q(dispositivo_ref__ta_id=self.kwargs['ta_id'])).\
            select_related(
            'dispositivo_base',
            'dispositivo_base__ta',
            'dispositivo_base__dispositivo_pai',
            'dispositivo_base__dispositivo_pai__ta', 'tipo')

        context['citado'] = {}
        for c in citado:
            if c.dispositivo_ref_id not in context['citado']:
                context['citado'][c.dispositivo_ref_id] = []
            context['citado'][c.dispositivo_ref_id].append(c)

        notas = Nota.objects.filter(
            dispositivo__ta_id=self.kwargs['ta_id']).select_related(
            'owner', 'tipo')

        context['notas'] = {}
        for n in notas:
            if n.dispositivo_id not in context['notas']:
                context['notas'][n.dispositivo_id] = []
            context['notas'][n.dispositivo_id].append(n)

        tas_pub = [d.ta_publicado for d in self.object_list if d.ta_publicado]
        tas_pub = set(tas_pub)
        ta_pub_list = {}
        for ta in tas_pub:
            ta_pub_list[ta.pk] = str(ta)
        context['ta_pub_list'] = ta_pub_list

        # context['vigencias'] = self.get_vigencias()

        return context

    def get_queryset(self):
        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1

        self.inicio_vigencia = None
        self.fim_vigencia = None
        self.ta_vigencia = None
        if 'sign' in self.kwargs:
            signer = Signer()
            try:
                string = signer.unsign(self.kwargs['sign']).split(',')
                self.ta_vigencia = int(string[0])
                self.inicio_vigencia = parse_date(string[1])
                self.fim_vigencia = parse_date(string[2])
            except:
                return Dispositivo.objects.filter(
                    ordem__gt=0,
                    ta_id=self.kwargs['ta_id'],
                ).select_related(*DISPOSITIVO_SELECT_RELATED)

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
                ano = item.ta_publicado.ano if item.ta_publicado else\
                    item.ta.ano
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


class TextEditView(CompMixin, TemplateView):
    template_name = 'compilacao/text_edit.html'

    def has_permission(self):
        self.object = self.ta
        return self.object.has_edit_permission(self.request)

    def get(self, request, *args, **kwargs):

        if self.object.editing_locked:
            if 'unlock' not in request.GET:
                messages.error(
                    request, _(
                        'A edição deste Texto Articulado está bloqueada.'))
                return redirect(to=reverse_lazy(
                    'sapl.compilacao:ta_text', kwargs={
                        'ta_id': self.object.id}))
            else:
                # TODO - implementar logging de ação de usuário
                self.object.editing_locked = False
                self.object.privacidade = STATUS_TA_EDITION
                self.object.save()
                messages.success(request, _(
                    'Texto Articulado desbloqueado com sucesso.'))

                if self.object.content_object:
                    self.object.content_object.save()

        else:
            if 'lock' in request.GET:

                # TODO - implementar logging de ação de usuário
                notificacoes = self.get_notificacoes(
                    object_list=self.object.dispositivos_set.all(),
                    type_notificacoes=['danger', ])

                if notificacoes:
                    messages.error(
                        request,
                        _('Existem erros a serem corrigidos que impedem a '
                          'publicação deste Texto Articulado. '
                          'Corrija os erros apontados nas notificações.'))
                    self.request.session[
                        'type_notificacoes'] = ['danger', ]
                    return redirect(to=reverse_lazy(
                        'sapl.compilacao:ta_text_notificacoes', kwargs={
                            'ta_id': self.object.id}))

                self.object.editing_locked = True
                self.object.privacidade = STATUS_TA_PUBLIC
                self.object.save()
                messages.success(request, _(
                    'Texto Articulado bloqueado com sucesso.'))

                if self.object.content_object:
                    self.object.content_object.save()

                return redirect(to=reverse_lazy(
                    'sapl.compilacao:ta_text', kwargs={
                        'ta_id': self.object.id}))

        return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        dispositivo_id = int(self.kwargs['dispositivo_id']) \
            if 'dispositivo_id' in self.kwargs else 0

        if dispositivo_id:
            self.object = Dispositivo.objects.get(pk=dispositivo_id)

        context = super(TemplateView, self).get_context_data(**kwargs)

        if not dispositivo_id:
            ta = TextoArticulado.objects.get(pk=self.kwargs['ta_id'])
            self.object = ta

        context['object'] = self.object
        context['dispositivos_list'] = self.dispositivos_list()

        if 'action' in self.request.GET:
            context['action'] = self.request.GET['action']

        return context

    def dispositivos_list(self):
        self.runBase()

        tds = {td.pk: td for td in TipoDispositivo.objects.all()}

        dispositivo_id = int(self.kwargs['dispositivo_id']) \
            if 'dispositivo_id' in self.kwargs else 0
        ta_id = int(self.kwargs['ta_id']) \
            if 'ta_id' in self.kwargs else 0

        q = Q(ta_id=ta_id)

        dispositivos_de_alteracao = []
        dispositivos = []
        if dispositivo_id:
            bloco = Dispositivo.objects.get(pk=dispositivo_id)

            if (tds[bloco.tipo_dispositivo_id].dispositivo_de_alteracao and
                    not tds[bloco.tipo_dispositivo_id
                            ].dispositivo_de_articulacao) or (
                    bloco.ta_id != ta_id and bloco.ta_publicado_id == ta_id):
                dispositivos = [bloco, ]
            else:
                proximo_bloco = Dispositivo.objects.filter(
                    ordem__gt=bloco.ordem,
                    nivel__lte=bloco.nivel,
                    ta_id=ta_id)[:1]

                if not proximo_bloco.exists():
                    q = q & Q(ordem__gte=bloco.ordem)
                else:
                    q = q & Q(ordem__gte=bloco.ordem) & \
                        Q(ordem__lt=proximo_bloco[0].ordem)

                dispositivos_de_alteracao = Dispositivo.objects.filter(
                    ta_id=ta_id,
                    tipo_dispositivo__dispositivo_de_alteracao=True,
                    tipo_dispositivo__dispositivo_de_articulacao=False
                ).select_related(*DISPOSITIVO_SELECT_RELATED_EDIT)

        if not dispositivos:
            dispositivos = Dispositivo.objects.filter(
                q).select_related(*DISPOSITIVO_SELECT_RELATED_EDIT)

        dispositivos_alterados = Dispositivo.objects.filter(
            ta_publicado_id=ta_id)

        dispositivos_alteradores = Dispositivo.objects.filter(
            dispositivos_alterados_set__ta_id=ta_id)

        dpts = list(dispositivos) + \
            list(dispositivos_de_alteracao) + \
            list(dispositivos_alterados) + \
            list(dispositivos_alteradores)

        tas_pub = [d.ta_publicado for d in dispositivos if d.ta_publicado]
        tas_pub = set(tas_pub)
        lista_ta_publicado = {}
        for ta in tas_pub:
            lista_ta_publicado[ta.pk] = str(ta)

        dpts = {d.pk: {
                'dpt': d,
                'filhos': [],
                'alts': [],
                'pai': None,
                'st': None,                        # dispositivo substituido
                'sq': None,                        # dispositivo subsequente
                'da': None,                        # dispositivo atualizador
                'td': tds[d.tipo_dispositivo_id],  # tipo do dispositivo
                'na': self.nota_alteracao(d, lista_ta_publicado)\
                if d.ta_id == ta_id else None
                } for d in dpts}

        apagar = []
        for d in dispositivos:
            try:
                if d.dispositivo_substituido_id:
                    dpts[d.pk]['st'] = dpts[d.dispositivo_substituido_id]
            except:
                pass
            try:
                if d.dispositivo_subsequente_id:
                    dpts[d.pk]['sq'] = dpts[d.dispositivo_subsequente_id]
            except:
                pass
            try:
                if d.dispositivo_atualizador_id:
                    dpts[d.pk]['da'] = dpts[d.dispositivo_atualizador_id]
            except:
                pass
            try:
                if d.dispositivo_pai_id:
                    """ Pode não ser possível vincular a estrutura do pai
                    devido a busca de bloco não envolver o pai do bloco,
                    por isso os try's except's"""
                    dpts[d.pk]['pai'] = dpts[d.dispositivo_pai_id]

                    if tds[d.tipo_dispositivo_id].\
                            dispositivo_de_alteracao and not\
                            tds[d.tipo_dispositivo_id].\
                            dispositivo_de_articulacao:
                        apagar.append(d.pk)
                    else:
                        dpts[d.dispositivo_pai_id]['filhos'].append(dpts[d.pk])
                        apagar.append(d.pk)
            except:
                pass
            try:
                if tds[d.tipo_dispositivo_id].dispositivo_de_alteracao and\
                        tds[d.tipo_dispositivo_id].dispositivo_de_articulacao:

                    alts = Dispositivo.objects.values_list(
                        'pk', flat=True).order_by(
                        'ordem_bloco_atualizador').filter(
                        Q(dispositivo_pai_id=d.pk) |
                        Q(dispositivo_atualizador_id=d.pk))

                    for dAlt in alts:
                        dpts[d.pk]['alts'].append(dpts[dAlt])
                        dpts[dAlt]['da'] = dpts[d.pk]
            except:
                pass

        for pk in apagar:
            del dpts[pk]

        r = []
        for dd in dispositivos:
            if dd.pk in dpts:
                r.append(dpts[dd.pk])
        return r

    def nota_alteracao(self, dispositivo, lista_ta_publicado):
        if dispositivo.ta_publicado_id:
            d = dispositivo.dispositivo_atualizador.dispositivo_pai

            ta_publicado = lista_ta_publicado[dispositivo.ta_publicado_id] if\
                lista_ta_publicado else dispositivo.ta_publicado

            if dispositivo.dispositivo_de_revogacao:
                return _('Revogado pelo %s - %s.') % (
                    d, ta_publicado)
            elif not dispositivo.dispositivo_substituido_id:
                return _('Inclusão feita pelo %s - %s.') % (
                    d, ta_publicado)
            else:
                return _('Alteração feita pelo %s - %s.') % (
                    d, ta_publicado)

        return ''

    def runBase(self):
        result = Dispositivo.objects.filter(ta_id=self.kwargs['ta_id'])

        if not result.exists():
            # FIXME a inserção básica deve ser refatorada para não depender
            # das classes css

            ta = self.object
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
            a.save()

            return

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
            e.texto = ta.ementa
            e.dispositivo_pai = a
            e.save()

            a.pk = None
            a.nivel = 0
            a.ordem = e.ordem + Dispositivo.INTERVALO_ORDEM
            a.ordem_bloco_atualizador = 0
            a.set_numero_completo([2, 0, 0, 0, 0, 0, ])
            a.save()


class ActionsCommonsMixin:

    def set_message(self, data, _type, message, time=None, modal=False):
        data['message'] = {
            'type': _type,
            'value': str(message)}
        if time:
            data['message']['time'] = time
        data['message']['modal'] = modal
        return

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


class ActionDragAndMoveDispositivoAlteradoMixin(ActionsCommonsMixin):

    def json_drag_move_dpt_alterado(self, context):

        bloco = Dispositivo.objects.get(pk=self.request.GET['bloco_pk'])
        dpt = Dispositivo.objects.get(pk=self.kwargs['dispositivo_id'])

        if dpt.tipo_dispositivo.dispositivo_de_alteracao:
            dpt.dispositivo_pai = bloco
        else:
            dpt.dispositivo_atualizador = bloco

        filhos = Dispositivo.objects.order_by(
            'ordem_bloco_atualizador').filter(
            Q(dispositivo_pai_id=bloco.pk) |
            Q(dispositivo_atualizador_id=bloco.pk))

        if not filhos.exists():
            dpt.ordem_bloco_atualizador = Dispositivo.INTERVALO_ORDEM
        else:
            index = int(self.request.GET['index'])
            fpks = filhos.values_list(
                'pk', flat=True).order_by('ordem_bloco_atualizador')

            index_dpt = 0
            try:
                index_dpt = list(fpks).index(dpt.pk)
            except:
                pass

            filho_index = filhos[
                index if index_dpt >= index
                else index + 1] if (
                index if index_dpt >= index
                else index + 1) < filhos.count() else filhos.last()
            if filhos.last() == filho_index:
                dpt.ordem_bloco_atualizador = \
                    filho_index.ordem_bloco_atualizador + 1
            else:
                dpt.ordem_bloco_atualizador = \
                    filho_index.ordem_bloco_atualizador - 1

        dpt.save()
        bloco.ordenar_bloco_alteracao()

        return {}


class ActionDeleteDispositivoMixin(ActionsCommonsMixin):

    def json_delete_item_dispositivo(self, context):
        return self.json_delete_bloco_dispositivo(context, bloco=False)

    def json_delete_bloco_dispositivo(self, context, bloco=True):
        base = Dispositivo.objects.get(pk=self.kwargs['dispositivo_id'])
        ta_base = base.ta

        base_anterior = Dispositivo.objects.order_by('-ordem').filter(
            ta_id=base.ta_id,
            ordem__lt=base.ordem
        ).first()

        data = {}
        if base_anterior:
            data = self.get_json_for_refresh(base_anterior)
        else:
            base_anterior = base.get_nivel_zero_anterior()
            data = self.get_json_for_refresh(base_anterior)

        data['pai'] = [base.get_raiz().pk]

        if ta_base.id != int(self.kwargs['ta_id']):
            data['pai'] = [base.dispositivo_atualizador.pk]
            data['pk'] = base.dispositivo_atualizador.pk

        try:
            with transaction.atomic():
                message = str(self.remover_dispositivo(base, bloco))
                if message:
                    self.set_message(data, 'warning', message, modal=True)
                else:
                    self.set_message(data, 'success', _(
                        'Exclusão efetuada com sucesso!'), modal=True)
                ta_base.reagrupar_ordem_de_dispositivos()
        except Exception as e:
            data['pk'] = self.kwargs['dispositivo_id']
            self.set_message(data, 'danger', str(e), modal=True)

        return data

    def remover_dispositivo(self, base, bloco):
        base_ordem = base.ordem
        if base.dispositivo_subsequente or base.dispositivo_substituido:
            p = base.dispositivo_substituido
            n = base.dispositivo_subsequente

            if n:
                # print(n.id, n)
                n.dispositivo_substituido = p
                n.save()

            if p:
                # print(p.id, p)
                p.dispositivo_subsequente = n
                if n:
                    p.fim_vigencia = n.inicio_vigencia - timedelta(days=1)
                    p.fim_eficacia = n.inicio_eficacia - timedelta(days=1)
                else:
                    p.fim_vigencia = None
                    p.fim_eficacia = None

                try:
                    for d in base.dispositivos_filhos_set.all():
                        p.dispositivos_filhos_set.add(d)
                    p.save()
                except Exception as e:
                    print(e)
            base.delete()
        else:
            proxima_articulacao = base.get_proximo_nivel_zero()
            if not bloco:
                # tranferir filhos para primeiro pai possível acima da base
                # de exclusão
                for d in base.dispositivos_filhos_set.all():
                    # inserções automáticas são excluidas junto com sua base,
                    # independente da escolha do usuário

                    """ TODO: Criar possibilidade de transferência de filhos
                    de dispositivos automáticos
                    ex: na exclusão de artigos, na versão atual,
                    os caputs serão excluidos automáticamente mesmo que a
                    exclusão não seja em bloco. O que fazer com os incisos?
                    transferir para o caput imediatamente acima visto se
                    tratar de uma exclusão de item?"""
                    d_nivel_old = d.nivel
                    if d.auto_inserido:
                        d.delete()
                        continue

                    # encontrar possível pai que será o primeiro parent
                    # possível dos parents do dispostivo
                    # imediatamente anterior ao dispositivo base

                    anterior = Dispositivo.objects.order_by('-ordem').filter(
                        ta_id=base.ta_id,
                        ordem__lt=d.ordem).exclude(
                        pk=base.pk).exclude(
                        dispositivo_pai=base).first()

                    if not anterior:
                        raise Exception(
                            _('Não é possível excluir este Dispositivo sem'
                              ' excluir toda a sua estrutura!!!'))

                    if anterior.tipo_dispositivo == d.tipo_dispositivo:
                        d.dispositivo_pai = anterior.dispositivo_pai
                        d.nivel = anterior.nivel
                        if not d.tipo_dispositivo.contagem_continua:
                            d.set_numero_completo(
                                anterior.get_numero_completo())

                            if d.dispositivo_substituido != anterior:
                                d.transform_in_next()
                            d.rotulo = d.rotulo_padrao()
                    else:
                        parents = [anterior, ] + anterior.get_parents()

                        for candidato in parents:
                            if candidato == base:
                                raise Exception(
                                    _('Não é possível excluir este '
                                      'Dispositivo sem '
                                      'excluir toda a sua estrutura!!!'))
                            if (candidato.tipo_dispositivo ==
                                    d.tipo_dispositivo):
                                d.dispositivo_pai = candidato.dispositivo_pai
                                d.nivel = candidato.nivel
                                if not d.tipo_dispositivo.contagem_continua:
                                    d.set_numero_completo(
                                        candidato.get_numero_completo())
                                    if d.dispositivo_substituido != candidato:
                                        d.transform_in_next()
                                    d.rotulo = d.rotulo_padrao()
                                break

                            elif (candidato.tipo_dispositivo ==
                                  d.dispositivo_pai.tipo_dispositivo):
                                d.dispositivo_pai = candidato
                                d.nivel = candidato.nivel + 1
                                break

                            elif d.tipo_dispositivo.possiveis_pais.filter(
                                    pai=candidato.tipo_dispositivo,
                                    perfil__padrao=True).exists():
                                d.dispositivo_pai = candidato
                                if ';' in d.tipo_dispositivo.\
                                        rotulo_prefixo_texto:
                                    d.set_numero_completo([0, 0, 0, 0, 0, 0, ])
                                else:
                                    d.set_numero_completo([1, 0, 0, 0, 0, 0, ])
                                d.nivel = candidato.nivel + 1
                                d.rotulo = d.rotulo_padrao()
                                break
                        else:

                            raise Exception(
                                _('Não é possível excluir este '
                                  'Dispositivo sem '
                                  'excluir toda a sua estrutura!!!'))

                        if not parents:
                            d.dispositivo_pai = anterior
                            d.nivel = anterior.nivel + 1

                    d.save(clean=False)
                    if d.nivel != d_nivel_old:
                        d.organizar_niveis()

                pai_base = base.dispositivo_pai
                if pai_base:
                    # Localizar irmaos posteriores do mesmo tipo de base
                    # se não DCC
                    if not base.tipo_dispositivo.contagem_continua:
                        irmaos_posteriores = pai_base.dispositivos_filhos_set.\
                            filter(
                                ordem__gt=base_ordem,
                                tipo_dispositivo=base.tipo_dispositivo)

                    # se DCC
                    else:
                        irmaos_posteriores = Dispositivo.objects.order_by(
                            'ordem').filter(
                            ta_id=base.ta_id,
                            ordem__gt=base_ordem,
                            tipo_dispositivo_id=base.tipo_dispositivo_id)

                        if proxima_articulacao:
                            irmaos_posteriores = irmaos_posteriores.exclude(
                                ordem__gte=proxima_articulacao.ordem)

                    # excluir e renumerar irmaos
                    profundidade_base = base.get_profundidade()
                    base.delete()

                    for irmao in irmaos_posteriores:
                        irmao.transform_in_prior(
                            profundidade=profundidade_base)
                        irmao.rotulo = irmao.rotulo_padrao()
                        irmao.save()

                    irmaos = pai_base.dispositivos_filhos_set.\
                        filter(tipo_dispositivo=base.tipo_dispositivo)

                    if (irmaos.count() == 1 and
                            ';' in irmaos[0].
                            tipo_dispositivo.rotulo_prefixo_texto):
                        i = irmaos[0]
                        i.set_numero_completo([0, 0, 0, 0, 0, 0, ])
                        i.rotulo = i.rotulo_padrao(local_insert=1)
                        i.save()
                else:
                    # Renumerar Dispostivos de Contagem Contínua
                    # de dentro da base se pai
                    dcc = Dispositivo.objects.order_by('ordem').filter(
                        ta_id=base.ta_id,
                        ordem__gt=base.ordem,
                        tipo_dispositivo__contagem_continua=True)

                    if proxima_articulacao:
                        dcc = dcc.exclude(
                            ordem__gte=proxima_articulacao.ordem)

                    base_adicao = {}

                    nivel_zero_anterior = base.get_nivel_zero_anterior()
                    if nivel_zero_anterior:
                        nivel_zero_anterior = nivel_zero_anterior.ordem
                    else:
                        nivel_zero_anterior = 0

                    dcc = list(dcc)
                    for d in dcc:  # ultimo DCC do tipo encontrado

                        if d.tipo_dispositivo.class_css not in base_adicao:
                            ultimo_dcc = Dispositivo.objects.order_by(
                                'ordem').filter(
                                ta_id=base.ta_id,
                                ordem__lt=base.ordem,
                                ordem__gt=nivel_zero_anterior,
                                tipo_dispositivo__contagem_continua=True,
                                tipo_dispositivo=d.tipo_dispositivo).last()

                            if not ultimo_dcc:
                                break

                            base_adicao[
                                d.tipo_dispositivo.class_css] = ultimo_dcc.\
                                dispositivo0

                        d.dispositivo0 += base_adicao[
                            d.tipo_dispositivo.class_css]

                        d.rotulo = d.rotulo_padrao()
                    dcc.reverse()
                    for d in dcc:
                        d.save()

                    base.delete()

            # em Bloco
            else:

                # Religar numeração de dispositivos de contagem contínua
                # que serão excluidos
                # pbi - proxima base independente
                pbi = Dispositivo.objects.\
                    order_by('ordem').filter(
                        ta_id=base.ta_id,
                        ordem__gt=base_ordem,
                        nivel__lte=base.nivel).first()

                if pbi:
                    dcc_a_excluir = Dispositivo.objects.order_by(
                        'ordem').filter(
                        ta_id=base.ta_id,
                        ordem__gte=base_ordem,
                        ordem__lt=pbi.ordem,
                        tipo_dispositivo__contagem_continua=True)

                    if proxima_articulacao:
                        dcc_a_excluir = dcc_a_excluir.exclude(
                            ordem__gte=proxima_articulacao.ordem)

                    religado = {}

                    for d in dcc_a_excluir:
                        if d.tipo_dispositivo.class_css in religado:
                            continue
                        religado[
                            d.tipo_dispositivo.class_css] = d.dispositivo0

                        dcc_a_religar = Dispositivo.objects.filter(
                            ta_id=d.ta_id,
                            ordem__gte=pbi.ordem,
                            tipo_dispositivo=d.tipo_dispositivo)

                        if proxima_articulacao:
                            dcc_a_religar = dcc_a_religar.exclude(
                                ordem__gte=proxima_articulacao.ordem)

                        primeiro_a_religar = 0
                        for dr in dcc_a_religar:
                            if not primeiro_a_religar:
                                primeiro_a_religar = dr.dispositivo0
                                base.delete()

                            dr.dispositivo0 = (
                                dr.dispositivo0 -
                                primeiro_a_religar + d.dispositivo0)
                            dr.rotulo = dr.rotulo_padrao()
                            dr.save(clean=base != dr)

                if base.tipo_dispositivo.dispositivo_de_alteracao:
                    dpts = base.dispositivos_alterados_set.all().order_by(
                        '-ordem_bloco_atualizador')
                    for dpt in dpts:
                        self.remover_dispositivo(dpt, False)

                if base.pk:
                    base.delete()

        return ''


class ActionDispositivoCreateMixin(ActionsCommonsMixin):

    def allowed_inserts(self, _base=None):
        request = self.request
        try:
            base = Dispositivo.objects.get(
                pk=self.kwargs['dispositivo_id'] if not _base else _base)

            result = [{'tipo_insert': force_text(string_concat(
                _('Inserir Após'),
                ' ',
                base.tipo_dispositivo.nome)),
                'icone': '&#8631;&nbsp;',
                'action': 'json_add_next',
                'itens': []},
                {'tipo_insert': force_text(string_concat(
                    _('Inserir em'),
                    ' ',
                    base.tipo_dispositivo.nome)),
                 'icone': '&#8690;&nbsp;',
                 'action': 'json_add_in',
                 'itens': []},
                {'tipo_insert': force_text(_('Inserir Antes')),
                 'icone': '&#8630;&nbsp;',
                 'action': 'json_add_prior',
                 'itens': []}]

            perfil_pk = request.session['perfil_estrutural']

            prox_possivel = Dispositivo.objects.filter(
                ordem__gt=base.ordem,
                nivel__lte=base.nivel,
                ta_id=base.ta_id)[:1]

            if prox_possivel.exists():
                prox_possivel = prox_possivel[0]
            else:
                prox_possivel = None

            # Possíveis inserções de nível já existentes
            parents = base.get_parents()
            parents.insert(0, base)
            nivel = sys.maxsize
            for dp in parents:

                if dp.nivel >= nivel:
                    continue

                if dp.auto_inserido:
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
                        'provavel': '%s <small>(%s)</small>' % (
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
                              'provavel': '%s <small>(%s)</small>' % (
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

                    if td.dispositivo_de_alteracao:
                        if not self.request.user.has_perm(
                                'compilacao.'
                                'change_dispositivo_registros_compilacao'):
                            continue

                    if paradentro and not td.permitido_inserir_in(
                        tipb,
                        include_relative_autos=True,
                            perfil_pk=perfil_pk):
                        continue

                    base.tipo_dispositivo = td

                    if not paradentro:

                        flag_insercao = False
                        for possivelpai in parents:
                            if td.permitido_inserir_in(
                                possivelpai.tipo_dispositivo,
                                include_relative_autos=True,
                                    perfil_pk=perfil_pk):
                                flag_insercao = True
                                break

                        if not flag_insercao:
                            continue

                        if possivelpai.auto_inserido:
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

                    r = []

                    flag_pv = td.permitido_variacao(tipb, perfil_pk=perfil_pk)

                    if td.contagem_continua and flag_pv:
                        flag_direcao = 1
                        flag_variacao = 0
                        while True:
                            if base.dispositivo0 == 0:
                                local_insert = 1
                            else:
                                local_insert = 0

                            rt = base.transform_in_next(flag_direcao)
                            if not rt[0]:
                                break
                            flag_variacao += rt[1]
                            r.append({'class_css': td.class_css,
                                      'tipo_pk': td.pk,
                                      'variacao': flag_variacao,
                                      'provavel': '%s <small>(%s)</small>' % (
                                          base.rotulo_padrao(local_insert),
                                          base.tipo_dispositivo.nome,),
                                      'dispositivo_base': base.pk})

                            flag_direcao = -1

                        r.reverse()

                        if len(r) > 0 and td.formato_variacao0 == \
                                TipoDispositivo.FNCN:
                            r = [r[0], ]
                    else:
                        if td.contagem_continua:
                            base.transform_in_next()
                        r = [{'class_css': td.class_css,
                              'tipo_pk': td.pk,
                              'variacao': 0,
                              'provavel': '%s <small>(%s)</small>' % (
                                  base.rotulo_padrao(1, paradentro),
                                  td.nome,),
                              'dispositivo_base': base.pk}]

                    if paradentro == 1:
                        result[1]['itens'] += r
                    else:
                        result[2]['itens'] += r
                        result[0]['itens'] += r

            # FIXME para liberar as opções de inserção antes,
            # o método json_add_prior deve ser implementado
            if len(result) > 2:
                result.pop()

            return result

        except Exception as e:
            print(e)

        return {}

    def json_set_dvt(self, context):
        # Dispositivo de Vigência do Texto Original e de Dpts Alterados
        dvt = Dispositivo.objects.get(pk=self.kwargs['dispositivo_id'])

        if dvt.auto_inserido:
            dvt = dvt.dispositivo_pai

        try:
            Dispositivo.objects.filter(
                ta=dvt.ta, ta_publicado__isnull=True
            ).update(
                dispositivo_vigencia=dvt,
                inicio_vigencia=dvt.inicio_vigencia,
                inicio_eficacia=dvt.inicio_eficacia)

            Dispositivo.objects.filter(ta_publicado=dvt.ta
                                       ).update(
                dispositivo_vigencia=dvt,
                inicio_vigencia=dvt.inicio_eficacia,
                inicio_eficacia=dvt.inicio_eficacia)

            dps = Dispositivo.objects.filter(dispositivo_vigencia=dvt)
            for d in dps:
                if d.dispositivo_substituido:
                    ds = d.dispositivo_substituido
                    ds.fim_vigencia = d.inicio_vigencia - timedelta(days=1)
                    ds.fim_eficacia = d.inicio_eficacia - timedelta(days=1)
                    ds.save()

                if d.dispositivo_subsequente:
                    ds = d.dispositivo_subsequente
                    d.fim_vigencia = ds.inicio_vigencia - timedelta(days=1)
                    d.fim_eficacia = ds.inicio_eficacia - timedelta(days=1)
                    d.save()

            data = {'pk': dvt.pk,
                    'pai': [dvt.pk, ]}
            self.set_message(data, 'success',
                             _('Dispositivo de Vigência atualizado '
                               'com sucesso!!!'))

            return data
        except:
            data = {}
            self.set_message(data,
                             'success',
                             _('Ocorreu um erro na atualização do '
                               'Dispositivo de Vigência'))

            return data

    def json_add_prior(self, context):
        return {}

    def json_add_in(self, context):
        return self.json_add_next(context, local_add='json_add_in')

    def json_add_next(
            self,
            context, local_add='json_add_next', create_auto_inserts=True):
        try:

            dp_auto_insert = None
            base = Dispositivo.objects.get(pk=self.kwargs['dispositivo_id'])
            tipo = TipoDispositivo.objects.get(pk=context['tipo_pk'])
            pub_last = Publicacao.objects.order_by(
                'data', 'hora').filter(ta=base.ta).last()

            variacao = int(context['variacao'])
            parents = [base, ] + base.get_parents()

            if 'perfil_pk' not in context:
                perfil_padrao = PerfilEstruturalTextoArticulado.objects.filter(
                    padrao=True).first()
                if perfil_padrao:
                    context['perfil_pk'] = perfil_padrao.pk
                else:
                    raise Exception('Não existe perfil padrão!')

            perfil_parents = PerfilEstruturalTextoArticulado.objects.get(
                pk=context['perfil_pk'])
            perfil_parents = perfil_parents.parents + [perfil_parents, ]
            perfil_parents.reverse()

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
                        ordem__gte=parents[-1].ordem,
                        tipo_dispositivo_id=tipo.pk,
                        ta_id=base.ta_id).first()

                    dp.set_numero_completo(
                        [1, 0, 0, 0, 0, 0, ] if not ultimo_irmao else
                        ultimo_irmao.get_numero_completo())
                    if ultimo_irmao:
                        dp.transform_in_next(variacao)
                else:
                    if ';' in tipo.rotulo_prefixo_texto:
                        dp.set_numero_completo([0, 0, 0, 0, 0, 0, ])
                    else:
                        dp.set_numero_completo([1, 0, 0, 0, 0, 0, ])

            # verificar se existe restrição de quantidade de itens
            if dp.dispositivo_pai:
                for perfil in perfil_parents:
                    pp = dp.tipo_dispositivo.possiveis_pais.filter(
                        pai_id=dp.dispositivo_pai.tipo_dispositivo_id,
                        perfil=perfil)

                    if pp.exists() and pp[0].quantidade_permitida >= 0:
                        qtd_existente = Dispositivo.objects.filter(
                            ta_id=dp.ta_id,
                            tipo_dispositivo_id=dp.tipo_dispositivo_id,
                            dispositivo_pai=dp.dispositivo_pai).count()

                        if qtd_existente >= pp[0].quantidade_permitida:
                            data = {'pk': base.pk,
                                    'pai': [base.dispositivo_pai.pk, ]}
                            self.set_message(data, 'warning',
                                             _('Limite de inserções de '
                                               'dispositivos deste tipo '
                                               'foi excedido.'), time=6000)
                            return data

            ordem = base.criar_espaco(
                espaco_a_criar=1, local=local_add)

            dp.rotulo = dp.rotulo_padrao()
            dp.ordem = ordem
            dp.incrementar_irmaos(variacao, [local_add, ], force=False)

            dp.publicacao = pub_last
            dp.save()

            count_auto_insert = 0
            if create_auto_inserts:
                for perfil in perfil_parents:
                    tipos_dp_auto_insert = tipo.filhos_permitidos.filter(
                        filho_de_insercao_automatica=True,
                        perfil=perfil)

                    for tipoauto in tipos_dp_auto_insert:
                        qtdp = tipoauto.quantidade_permitida
                        if qtdp >= 0:
                            qtdp -= Dispositivo.objects.filter(
                                ta_id=dp.ta_id,
                                dispositivo_pai_id=dp.id,
                                tipo_dispositivo_id=tipoauto.filho_permitido.pk
                            ).count()
                            if qtdp > 0:
                                count_auto_insert += 1
                        else:
                            count_auto_insert += 1

                    if count_auto_insert:
                        break

            # Inserção automática
            if count_auto_insert:

                ordem = dp.criar_espaco(
                    espaco_a_criar=count_auto_insert, local='json_add_in')

                dp_pk = dp.pk
                dp.ordem = ordem
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

                    dp.publicacao = pub_last
                    dp.auto_inserido = True
                    dp.save()
                    dp_auto_insert = dp

                    ordem += Dispositivo.INTERVALO_ORDEM
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

                    if not filho.dispositivo_pai or\
                            filho.dispositivo_pai.ordem >= dp.ordem:
                        continue

                    nivel = filho.nivel

                    if not filho.tipo_dispositivo.permitido_inserir_in(
                        dp.tipo_dispositivo,
                            perfil_pk=context['perfil_pk']):
                        continue

                    filho.dispositivo_pai = dp
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
                    filho.save()

            ''' Renumerar dispositivos de
            contagem continua, caso a inserção seja uma articulação'''

            if dp.nivel == 0:

                proxima_articulacao = dp.get_proximo_nivel_zero()

                if not proxima_articulacao:
                    filhos_continuos = list(Dispositivo.objects.filter(
                        ordem__gt=dp.ordem,
                        ta_id=dp.ta_id,
                        tipo_dispositivo__contagem_continua=True))
                else:
                    filhos_continuos = list(Dispositivo.objects.filter(
                        ordem__gt=dp.ordem,
                        ordem__lt=proxima_articulacao.ordem,
                        ta_id=dp.ta_id,
                        tipo_dispositivo__contagem_continua=True))

                base_reducao = {}

                for filho in filhos_continuos:
                    if filho.tipo_dispositivo.class_css not in base_reducao:
                        base_reducao[filho.tipo_dispositivo.class_css] = \
                            filho.dispositivo0 - 1

                    filho.dispositivo0 -= base_reducao[
                        filho.tipo_dispositivo.class_css]

                    filho.rotulo = filho.rotulo_padrao()
                    filho.save()

            ''' Reordenar bloco atualizador caso a inserção seja
            dentro de um bloco de alteração'''

            if dp.tipo_dispositivo.dispositivo_de_alteracao and\
                    not dp.tipo_dispositivo.dispositivo_de_articulacao:
                dp.dispositivo_pai.ordenar_bloco_alteracao()

            if dp_auto_insert is None:
                data = self.get_json_for_refresh(dp)
            else:
                data = self.get_json_for_refresh(dp=dp, dpauto=dp_auto_insert)

            # data['action'] = 'get_form_base'
            return data

        except Exception as e:
            print(e)
            return {}


class ActionsEditMixin(ActionDragAndMoveDispositivoAlteradoMixin,
                       ActionDeleteDispositivoMixin,
                       ActionDispositivoCreateMixin):

    def render_to_json_response(self, context, **response_kwargs):

        action = getattr(self, context['action'])

        if 'tipo_pk' in self.request.GET:
            context['tipo_pk'] = self.request.GET['tipo_pk']

        if 'variacao' in self.request.GET:
            context['variacao'] = self.request.GET['variacao']

        if 'pk_bloco' in self.request.GET:
            context['pk_bloco'] = self.request.GET['pk_bloco']

        if 'perfil_estrutural' in self.request.session:
            context['perfil_pk'] = self.request.session['perfil_estrutural']

        data = action(context)

        if 'message' in context and 'message' not in data:
            data['message'] = context['message']

        return JsonResponse(data, safe=False)

    def json_get_perfis(self, context):
        data = {'pk': self.kwargs['dispositivo_id'],
                'pai': [self.kwargs['dispositivo_id'], ]}

        return data

    def update_perfis(self):
        qs = PerfilEstruturalTextoArticulado.objects.all()
        request = self.request

        ta = None
        if hasattr(self, 'object') and isinstance(self.object, Dispositivo):
            ta = self.object.ta
        elif hasattr(self, 'object') and isinstance(
                self.object, TextoArticulado):
            ta = self.object
        else:
            ta_id = self.kwargs.get('ta_id', 0)
            if ta_id:
                ta = TextoArticulado.objects.get(pk=ta_id)

        if ta:
            if ta.content_object and hasattr(ta.content_object, 'perfis'):
                qs = ta.content_object.perfis
            else:
                qs = ta.tipo_ta.perfis.all()

        perfil_get = request.GET.get('perfil_pk', 0)
        if perfil_get and qs.filter(id=perfil_get).exists():
            request.session['perfil_estrutural'] = int(perfil_get)
            return qs

        perfil_session = request.session.get('perfil_estrutural', perfil_get)
        if perfil_session and qs.filter(id=perfil_session).exists():
            request.session['perfil_estrutural'] = int(perfil_session)
            return qs

        if qs.exists():
            request.session['perfil_estrutural'] = qs.first().id

        return qs

    def json_add_next_registra_inclusao(
            self, context, local_add='json_add_next'):

        bloco_alteracao = Dispositivo.objects.get(pk=context['pk_bloco'])

        data = {}
        data.update({'pk': bloco_alteracao.pk,
                     'pai': [bloco_alteracao.pk, ]})

        """if bloco_alteracao.inicio_vigencia < base.inicio_vigencia:
            self.set_message(
                data, 'danger',
                _('O Dispositivo Base para inclusão possui início de vigência '
                  'anterior ao bloco de alteração atual. Um bloco de '
                  'alteração não pode ser retroativo!'), time=10000)
            return data"""

        data = self.json_add_next(context,
                                  local_add=local_add,
                                  create_auto_inserts=True)

        if data:

            ndp = Dispositivo.objects.get(pk=data['pk'])

            ndp.dispositivo_atualizador = bloco_alteracao
            ndp.ta_publicado = bloco_alteracao.ta
            ndp.publicacao = bloco_alteracao.publicacao
            ndp.dispositivo_vigencia = bloco_alteracao.dispositivo_vigencia
            if ndp.dispositivo_vigencia:
                ndp.inicio_eficacia = ndp.dispositivo_vigencia.inicio_eficacia
                ndp.inicio_vigencia = ndp.dispositivo_vigencia.inicio_vigencia
            else:
                ndp.inicio_eficacia = bloco_alteracao.inicio_eficacia
                ndp.inicio_vigencia = bloco_alteracao.inicio_vigencia

            dispositivos_do_bloco = \
                bloco_alteracao.dispositivos_alterados_set.order_by(
                    'ordem_bloco_atualizador')
            if dispositivos_do_bloco.exists():
                ndp.ordem_bloco_atualizador = dispositivos_do_bloco.last(
                ).ordem_bloco_atualizador + Dispositivo.INTERVALO_ORDEM

            ndp.save()
            bloco_alteracao.ordenar_bloco_alteracao()

            data.update({'pk': ndp.pk,
                         'pai': [bloco_alteracao.pk, ]})

        return data

    def json_add_in_registra_inclusao(self, context):
        return self.json_add_next_registra_inclusao(
            context, local_add='json_add_in')

    def registra_revogacao(self, bloco_alteracao, dispositivo_a_revogar):
        return self.registra_alteracao(
            bloco_alteracao,
            dispositivo_a_revogar,
            revogacao=True
        )

    def registra_alteracao(self,
                           bloco_alteracao,
                           dispositivo_a_alterar,
                           revogacao=False):
        """
        Caracteristicas:
        1 - Se é um dispositivo simples e sem subsequente
            - filhos devem ser transferidos

        2 - Se é um dispositivo simples com subsequente
            - não deveria ter filhos locais
            - substituidos e subsequentes devem ser religados

        3 - Se é um dispositivo articulado e sem subsequente
            - filhos locais devem ser transferidos

        4 - Se é um dispositivo articulado com subsequente
            - não deveria ter filhos locais

        5 - Alterações em dispositivo articulado só são relevantes para
            alteração de rótulo. O editor dinâmico não possibilita essa
            mudança, porém, após registro de alteração, a mudança de rótulo
            pode ser feita no editor avançado.
        """

        data = {}
        data.update({'pk': bloco_alteracao.pk,
                     'pai': [bloco_alteracao.pk, ]})

        history = dispositivo_a_alterar.history()

        for d in history:
            """FIXME: A comparação "<" deverá ser mudada para
                "<=" caso seja necessário permitir duas alterações
                com mesmo inicio_vigencia no mesmo dispositivo. Neste Caso,
                a sequencia correta ficará a cargo dos reposicionamentos e
                (a ser implementado) entre dispositivos de mesmo nível,
            """
            if d.inicio_vigencia < bloco_alteracao.inicio_vigencia:
                dispositivo_a_alterar = d
                break

        if (dispositivo_a_alterar.inicio_vigencia >
                bloco_alteracao.inicio_vigencia):
            self.set_message(
                data, 'danger',
                _('Não é possível alterar um Dispositivo com início de '
                  'Vigência posterior a data de Vigência do Dispositivo '
                  'Alterador!'), time=10000)
            return data

        if dispositivo_a_alterar.tipo_dispositivo.dispositivo_de_articulacao\
                and not revogacao:
            self.set_message(
                data, 'warning',
                _('Registrar alteração de um dispositivo de articulação '
                      'só é relevante para o caso de alterações de rótulo. '
                      'Se não é este o caso, a alteração deve ser específica '
                      'para o dispositivo que se quer alterar.'), modal=True)

        ndp = Dispositivo.new_instance_based_on(
            dispositivo_a_alterar, dispositivo_a_alterar.tipo_dispositivo)
        ndp.auto_inserido = dispositivo_a_alterar.auto_inserido
        ndp.rotulo = dispositivo_a_alterar.rotulo
        ndp.publicacao = bloco_alteracao.publicacao

        if not revogacao:
            ndp.texto = dispositivo_a_alterar.texto
        else:
            ndp.texto = Dispositivo.TEXTO_PADRAO_DISPOSITIVO_REVOGADO
            ndp.dispositivo_de_revogacao = True

        ndp.dispositivo_vigencia = bloco_alteracao.dispositivo_vigencia

        if ndp.dispositivo_vigencia:
            ndp.inicio_eficacia = ndp.dispositivo_vigencia.inicio_eficacia
            ndp.inicio_vigencia = ndp.dispositivo_vigencia.inicio_eficacia
        else:
            ndp.inicio_eficacia = bloco_alteracao.inicio_eficacia
            ndp.inicio_vigencia = bloco_alteracao.inicio_eficacia

        try:
            ordem = dispositivo_a_alterar.criar_espaco(
                espaco_a_criar=1, local='json_add_in')

            ndp.ordem = ordem
            ndp.dispositivo_atualizador = bloco_alteracao
            ndp.ta_publicado = bloco_alteracao.ta

            p = dispositivo_a_alterar
            n = dispositivo_a_alterar.dispositivo_subsequente

            ndp.dispositivo_substituido = p
            ndp.dispositivo_subsequente = n

            if n:
                ndp.fim_eficacia = n.inicio_eficacia - \
                    timedelta(days=1)
                ndp.fim_vigencia = n.inicio_vigencia - \
                    timedelta(days=1)

            # Coloca o novo dispostivo no final do bloco
            dispositivos_do_bloco = \
                bloco_alteracao.dispositivos_alterados_set.order_by(
                    'ordem_bloco_atualizador')

            if dispositivos_do_bloco.exists():
                ndp.ordem_bloco_atualizador = dispositivos_do_bloco.last(
                ).ordem_bloco_atualizador + Dispositivo.INTERVALO_ORDEM
            else:
                ndp.ordem_bloco_atualizador = Dispositivo.INTERVALO_ORDEM
            ndp.save()

            p.dispositivo_subsequente = ndp
            p.fim_eficacia = ndp.inicio_eficacia - timedelta(days=1)
            p.fim_vigencia = ndp.inicio_vigencia - timedelta(days=1)
            p.save()

            if n:
                # a ordem desse objeto foi alterada pela função criar_espaco
                # deve ser recarregado para atualização
                n.refresh_from_db()
                n.dispositivo_substituido = ndp
                n.save()

            filhos_diretos = dispositivo_a_alterar.dispositivos_filhos_set
            for d in filhos_diretos.all():
                d.dispositivo_pai = ndp
                d.save()

            ndp.ta.reordenar_dispositivos()
            bloco_alteracao.ordenar_bloco_alteracao()

            if not revogacao:
                if 'message' not in data:
                    self.set_message(
                        data, 'success',
                        _('Dispositivo de Alteração adicionado com sucesso.'))
            else:
                self.set_message(
                    data, 'success',
                    _('Dispositivo de Revogação adicionado com sucesso.'))

        except Exception as e:
            print(e)

        data.update({'pk': ndp.pk,
                     'pai': [bloco_alteracao.pk, ]})

        return data


class DispositivoDinamicEditView(
        ActionsEditMixin, TextEditView, UpdateView):
    template_name = 'compilacao/text_edit_bloco.html'
    model = Dispositivo
    form_class = DispositivoEdicaoBasicaForm

    def get_initial(self):
        initial = UpdateView.get_initial(self)

        if 'action' in self.request.GET:
            initial.update({'editor_type': self.request.GET['action']})

        if self.action.startswith('get_form_'):
            if self.action.endswith('_radio_allowed_inserts'):
                initial.update({'allowed_inserts': self.allowed_inserts()})

            initial.update({'texto_articulado_do_editor':
                            self.kwargs['ta_id']})

        initial.update({'dispositivo_search_form': reverse_lazy(
            'sapl.compilacao:dispositivo_search_form')})

        return initial

    def get_form(self, form_class=None):

        if self.action and self.action.startswith('get_form_'):
            if form_class is None:
                form_class = self.get_form_class()
            return form_class(**self.get_form_kwargs())
        else:
            return None

    def get(self, request, *args, **kwargs):

        if 'action' not in request.GET:
            self.action = None
            self.template_name = 'compilacao/text_edit_bloco.html'
            return TextEditView.get(self, request, *args, **kwargs)

        self.object = Dispositivo.objects.get(pk=self.kwargs['dispositivo_id'])
        perfil_estrutural_list = self.update_perfis()

        self.template_name = 'compilacao/ajax_form.html'
        self.action = request.GET['action']

        if self.action.startswith('get_form_'):
            if self.action.endswith('_base'):
                self.form_class = DispositivoEdicaoBasicaForm
            elif self.action.endswith('_alteracao'):
                self.form_class = DispositivoRegistroAlteracaoForm
            elif self.action.endswith('_revogacao'):
                self.form_class = DispositivoRegistroRevogacaoForm
            elif self.action.endswith('_inclusao'):
                self.form_class = DispositivoRegistroInclusaoForm

            context = self.get_context_data()
            return self.render_to_response(context)

        elif self.action.startswith('get_actions'):
            self.form_class = None

            ta_id = self.kwargs['ta_id']

            context = {}
            context['object'] = self.object

            if self.action.endswith('_allowed_inserts_registro_inclusao'):
                self.template_name = ('compilacao/'
                                      'ajax_actions_registro_inclusao.html')
                context['allowed_inserts'] = self.allowed_inserts()

            else:
                self.template_name = ('compilacao/'
                                      'ajax_actions_dinamic_edit.html')

                if ta_id == str(self.object.ta_id):
                    context['perfil_estrutural_list'] = perfil_estrutural_list
                    context['allowed_inserts'] = self.allowed_inserts()

            return self.render_to_response(context)

        elif self.action.startswith('json_'):
            context = self.get_context_data()
            return self.render_to_json_response(context)

        return JsonResponse({}, safe=False)

    def post(self, request, *args, **kwargs):

        d = Dispositivo.objects.get(
            pk=self.kwargs['dispositivo_id'])

        formtype = request.POST['formtype']
        if formtype == 'get_form_alteracao':

            dispositivo_a_alterar = Dispositivo.objects.get(
                pk=request.POST['dispositivo_alterado'])

            data = self.registra_alteracao(d, dispositivo_a_alterar)

        elif formtype == 'get_form_revogacao':

            dispositivo_a_revogar = Dispositivo.objects.get(
                pk=request.POST['dispositivo_revogado'])

            data = self.registra_revogacao(d, dispositivo_a_revogar)

        if formtype == 'get_form_inclusao':

            dispositivo_base_para_inclusao = Dispositivo.objects.get(
                pk=request.POST['dispositivo_base_para_inclusao'])

            data = self.registra_inclusao(d, dispositivo_base_para_inclusao)

        elif formtype == 'get_form_base':
            texto = request.POST['texto'].strip()
            texto_atualizador = request.POST['texto_atualizador'].strip()
            texto_atualizador = texto_atualizador \
                if texto != texto_atualizador else ''
            visibilidade = request.POST['visibilidade']

            # if d.texto != '':
            #    d.texto = texto
            #    d.save()
            #    return self.get(request, *args, **kwargs)
            d_texto = d.texto
            d.texto = texto.strip()
            d.texto_atualizador = texto_atualizador.strip()
            d.visibilidade = not visibilidade or visibilidade == 'True'
            d.save()

            if texto != '' and d.ta_id == int(self.kwargs['ta_id']):
                dnext = Dispositivo.objects.filter(
                    ta_id=d.ta_id,
                    ordem__gt=d.ordem,
                    texto='',
                    tipo_dispositivo__dispositivo_de_articulacao=False)[:1]

                if not dnext.exists():
                    dnext = []
                    dnext.append(d)
                    pais = [d.dispositivo_pai_id, ]
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

                data = {'pk': dnext[0].pk
                        if not d_texto else 0, 'pai': pais}
            elif d.ta_id != int(self.kwargs['ta_id']):
                data = {'pk': 0,
                        'pai': [d.dispositivo_atualizador_id, ]}
            else:
                data = {'pk': d.pk
                        if not d_texto or not d.texto else 0, 'pai': [d.pk, ]}

            self.set_message(data, 'success',
                             _('Dispositivo alterado com sucesso.'))

        return JsonResponse(data, safe=False)


class DispositivoSearchFragmentFormView(ListView):
    template_name = 'compilacao/dispositivo_form_search_fragment.html'

    def get(self, request, *args, **kwargs):

        if 'action' in request.GET and request.GET['action'] == 'get_tipos':
            result = choice_model_type_foreignkey_in_extenal_views(
                id_tipo_ta=request.GET['tipo_ta'])

            itens = []
            for i in result:
                item = {}
                item[i[0] if i[0] else ''] = str(i[1])
                itens.append(item)
            return JsonResponse(itens, safe=False)

        return ListView.get(self, request, *args, **kwargs)

    def get_queryset(self):
        try:
            n = 10
            if 'max_results' in self.request.GET:
                n = int(self.request.GET['max_results'])

            q = Q()
            if 'initial_ref' in self.request.GET:
                initial_ref = self.request.GET['initial_ref']
                if initial_ref:
                    q = q & Q(pk=initial_ref)

                result = Dispositivo.objects.filter(q).select_related(
                    'ta').exclude(
                    tipo_dispositivo__dispositivo_de_alteracao=True)

                return result[:n]

            str_texto = ''
            texto = ''
            rotulo = ''
            num_ta = ''
            ano_ta = ''

            if 'texto' in self.request.GET:
                str_texto = self.request.GET['texto']

            texto = str_texto.split(' ')

            if 'rotulo' in self.request.GET:
                rotulo = self.request.GET['rotulo']
                if rotulo:
                    q = q & Q(rotulo__icontains=rotulo)

            for item in texto:
                if not item:
                    continue
                if q:
                    q = q & (Q(texto__icontains=item) |
                             Q(texto_atualizador__icontains=item))
                else:
                    q = (Q(texto__icontains=item) |
                         Q(texto_atualizador__icontains=item))

            if 'tipo_ta' in self.request.GET:
                tipo_ta = self.request.GET['tipo_ta']
                if tipo_ta:
                    q = q & Q(ta__tipo_ta_id=tipo_ta)

            if 'num_ta' in self.request.GET:
                num_ta = self.request.GET['num_ta']
                if num_ta:
                    q = q & Q(ta__numero=num_ta)

            if 'ano_ta' in self.request.GET:
                ano_ta = self.request.GET['ano_ta']
                if ano_ta:
                    q = q & Q(ta__ano=ano_ta)

            if not q.children and not n:
                n = 10
            q = q & Q(nivel__gt=0)

            result = Dispositivo.objects.order_by(
                '-ta__data',
                '-ta__ano',
                '-ta__numero',
                'ta',
                'ordem').filter(q).select_related('ta')

            if 'data_type_selection' in self.request.GET and\
                    self.request.GET['data_type_selection'] == 'checkbox':
                result = result.exclude(
                    tipo_dispositivo__dispositivo_de_alteracao=True)
            else:
                if 'data_function' in self.request.GET and\
                        self.request.GET['data_function'] == 'alterador':
                    result = result.exclude(
                        tipo_dispositivo__dispositivo_de_alteracao=False,
                    )
                    result = result.exclude(
                        tipo_dispositivo__dispositivo_de_articulacao=False,
                    )
                    print(str(result.query))

            def resultados(r):
                if n:
                    return r[:n]
                else:
                    return r

                """if num_ta and ano_ta and not rotulo and not str_texto and\
                        'data_type_selection' in self.request.GET and\
                        self.request.GET['data_type_selection'] == 'checkbox':
                    return r
                else:
                    return r[:n]"""

            if 'tipo_model' not in self.request.GET:
                return resultados(result)

            tipo_model = self.request.GET['tipo_model']
            if not tipo_model:
                return resultados(result)

            integrations_view_names = get_integrations_view_names()

            tipo_ta = TipoTextoArticulado.objects.get(pk=tipo_ta)

            model_class = None
            for item in integrations_view_names:
                if hasattr(item, 'model_type_foreignkey') and\
                        hasattr(item, 'model'):
                    if (tipo_ta.content_type.model ==
                        item.model.__name__.lower() and
                            tipo_ta.content_type.app_label ==
                            item.model._meta.app_label):

                        model_class = item.model
                        model_type_class = item.model_type_foreignkey
                        tipo_model = item.model_type_foreignkey.objects.get(
                            pk=tipo_model)
                        break

            if not model_class:
                return resultados(result)

            column_field = ''
            for field in model_class._meta.fields:
                if field.related_model == model_type_class:
                    column_field = field.column
                    break

            if not column_field:
                return resultados(result)

            r = []

            """
            ao integrar um model ao app de compilação, se este model possuir

                texto_articulado = GenericRelation(
                    TextoArticulado, related_query_name='texto_articulado')

            será uma integração mais eficiente para as buscas de Dispositivos
            """
            if hasattr(model_class, 'texto_articulado'):
                q = q & Q(**{
                    'ta__texto_articulado__' + column_field: tipo_model.pk
                })
                if n:
                    result = result.filter(q)[:n]
                else:
                    result = result.filter(q)

            for d in result:
                if not d.ta.content_object or\
                        not hasattr(d.ta.content_object, column_field):
                    continue

                if tipo_model.pk == getattr(d.ta.content_object, column_field):
                    r.append(d)

                if (len(r) == n and (not num_ta or
                                     not ano_ta or rotulo or str_texto)):
                    break
            return r

        except Exception as e:
            print(e)


class DispositivoSearchModalView(FormView):
    template_name = 'compilacao/dispositivo_form_search.html'
    form_class = DispositivoSearchModalForm


class DispositivoEdicaoBasicaView(CompMixin, FormMessagesMixin, UpdateView):
    model = Dispositivo
    template_name = 'compilacao/dispositivo_form_edicao_basica.html'
    form_class = DispositivoEdicaoBasicaForm
    form_valid_message = _('Alterações no Dispositivo realizadas com sucesso!')
    form_invalid_message = _('Houve erro em registrar '
                             'as alterações no Dispositivo')

    permission_required = 'compilacao.change_dispositivo_edicao_avancada'

    @property
    def cancel_url(self):
        return reverse_lazy(
            'sapl.compilacao:ta_text_edit',
            kwargs={'ta_id': self.kwargs['ta_id']}) + '#' + str(self.object.pk)

    def get_success_url(self):
        return reverse_lazy(
            'sapl.compilacao:dispositivo_edit',
            kwargs={'ta_id': self.kwargs['ta_id'], 'pk': self.kwargs['pk']})

    def get_url_this_view(self):
        return 'sapl.compilacao:dispositivo_edit'

    def run_actions(self, request):
        if 'action' in request.GET and\
                request.GET['action'] == 'atualiza_rotulo':
            try:
                d = Dispositivo.objects.get(pk=self.kwargs['pk'])
                d.dispositivo0 = int(request.GET['dispositivo0'])
                d.dispositivo1 = int(request.GET['dispositivo1'])
                d.dispositivo2 = int(request.GET['dispositivo2'])
                d.dispositivo3 = int(request.GET['dispositivo3'])
                d.dispositivo4 = int(request.GET['dispositivo4'])
                d.dispositivo5 = int(request.GET['dispositivo5'])
                d.rotulo = d.rotulo_padrao()

                numero = d.get_numero_completo()[1:]

                zerar = False
                for i in range(len(numero)):
                    if not numero[i]:
                        zerar = True

                    if zerar:
                        numero[i] = 0

                if zerar:
                    d.set_numero_completo([d.dispositivo0, ] + numero)
                    d.rotulo = d.rotulo_padrao()

            except:
                return True, JsonResponse({'message': str(
                    _('Ocorreu erro na atualização do rótulo'))}, safe=False)
            return True, JsonResponse({
                'rotulo': d.rotulo,
                'dispositivo0': d.dispositivo0,
                'dispositivo1': d.dispositivo1,
                'dispositivo2': d.dispositivo2,
                'dispositivo3': d.dispositivo3,
                'dispositivo4': d.dispositivo4,
                'dispositivo5': d.dispositivo5}, safe=False)

        return False, ''

    def get(self, request, *args, **kwargs):

        flag_action, render_json_response = self.run_actions(request)
        if flag_action:
            return render_json_response

        return UpdateView.get(self, request, *args, **kwargs)


class DispositivoEdicaoVigenciaView(CompMixin, FormMessagesMixin, UpdateView):
    model = Dispositivo
    template_name = 'compilacao/dispositivo_form_vigencia.html'
    form_class = DispositivoEdicaoVigenciaForm
    form_valid_message = _('Alterações no Dispositivo realizadas com sucesso!')
    form_invalid_message = _('Houve erro em registrar '
                             'as alterações no Dispositivo')

    permission_required = 'compilacao.change_dispositivo_edicao_avancada'

    @property
    def cancel_url(self):
        return reverse_lazy(
            'sapl.compilacao:ta_text_edit',
            kwargs={'ta_id': self.kwargs['ta_id']}) + '#' + str(self.object.pk)

    def get_url_this_view(self):
        return 'sapl.compilacao:dispositivo_edit_vigencia'

    def get_success_url(self):
        return reverse_lazy(
            'sapl.compilacao:dispositivo_edit_vigencia',
            kwargs={'ta_id': self.kwargs['ta_id'], 'pk': self.kwargs['pk']})


class DispositivoDefinidorVigenciaView(CompMixin, FormMessagesMixin, FormView):
    model = Dispositivo
    template_name = 'compilacao/dispositivo_form_definidor_vigencia.html'
    form_class = DispositivoDefinidorVigenciaForm
    form_valid_message = _('Alterações no Dispositivo realizadas com sucesso!')
    form_invalid_message = _('Houve erro em registrar '
                             'as alterações no Dispositivo')

    permission_required = ('compilacao.change_dispositivo_edicao_avancada',
                           'compilacao.change_dispositivo_de_vigencia_global')

    def get_form_kwargs(self):
        kwargs = FormView.get_form_kwargs(self)
        kwargs.update({
            'pk': self.kwargs['pk'],
        })
        return kwargs

    @property
    def cancel_url(self):
        return reverse_lazy(
            'sapl.compilacao:ta_text_edit',
            kwargs={'ta_id': self.kwargs['ta_id']}) + '#' + str(self.object.pk)

    def get_url_this_view(self):
        return 'sapl.compilacao:dispositivo_edit_definidor_vigencia'

    def get_success_url(self):
        return reverse_lazy(
            'sapl.compilacao:dispositivo_edit_definidor_vigencia',
            kwargs={'ta_id': self.kwargs['ta_id'], 'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        self.object = get_object_or_404(Dispositivo, pk=kwargs['pk'])
        return FormView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = FormView.get_context_data(self, **kwargs)
        context.update({'object': self.object})
        return context

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Dispositivo, pk=kwargs['pk'])

        form = self.get_form()
        if form.is_valid():
            dvs = form.cleaned_data['dispositivo_vigencia']
            try:
                with transaction.atomic():
                    self.object.dispositivos_vigencias_set.clear()
                    for item in dvs:
                        d = Dispositivo.objects.get(pk=item)
                        self.object.dispositivos_vigencias_set.add(d)
                    return self.form_valid(form)
            except:
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)


class DispositivoEdicaoAlteracaoView(CompMixin, FormMessagesMixin, UpdateView):
    model = Dispositivo
    template_name = 'compilacao/dispositivo_form_alteracao.html'
    form_class = DispositivoEdicaoAlteracaoForm
    form_valid_message = _('Alterações no Dispositivo realizadas com sucesso!')
    form_invalid_message = _('Houve erro em registrar '
                             'as alterações no Dispositivo')

    permission_required = 'compilacao.change_dispositivo_registros_compilacao'

    @property
    def cancel_url(self):
        return reverse_lazy(
            'sapl.compilacao:ta_text_edit',
            kwargs={'ta_id': self.kwargs['ta_id']}) + '#' + str(self.object.pk)

    def get_url_this_view(self):
        return 'sapl.compilacao:dispositivo_edit_alteracao'

    def get_success_url(self):
        return reverse_lazy(
            'sapl.compilacao:dispositivo_edit_alteracao',
            kwargs={'ta_id': self.kwargs['ta_id'], 'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Dispositivo, pk=kwargs['pk'])

        form = self.get_form()
        if form.is_valid():
            try:
                with transaction.atomic():
                    return self.form_valid(form)
            except:
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)


class TextNotificacoesView(CompMixin, ListView, FormView):
    template_name = 'compilacao/text_notificacoes.html'
    form_class = TextNotificacoesForm

    permission_required = 'compilacao.view_dispositivo_notificacoes'

    def get(self, request, *args, **kwargs):
        self.object = TextoArticulado.objects.get(pk=self.kwargs['ta_id'])
        return super(TextNotificacoesView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = TextoArticulado.objects.get(pk=self.kwargs['ta_id'])
        return FormView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if 'object' not in kwargs:
            kwargs['object'] = self.object
        return ListView.get_context_data(self, **kwargs)

    def get_success_url(self):
        return reverse_lazy('sapl.compilacao:ta_text_notificacoes',
                            kwargs=self.kwargs)

    def get_initial(self):
        initial = {}

        if self.request.method == 'POST':
            if 'type_notificacoes' in self.request.POST:
                self.request.session[
                    'type_notificacoes'] = self.request.POST.getlist(
                    'type_notificacoes')
            else:
                self.request.session['type_notificacoes'] = []
        elif 'type_notificacoes' in self.request.session:
            initial['type_notificacoes'] = self.request.session[
                'type_notificacoes']
        else:
            initial['type_notificacoes'] = []

        return initial

    def get_queryset(self):

        result = Dispositivo.objects.filter(
            ta_id=self.kwargs['ta_id']
        ).select_related(*DISPOSITIVO_SELECT_RELATED)

        type_notificacoes = []
        if 'type_notificacoes' in self.request.session:
            type_notificacoes = self.request.session['type_notificacoes']

        if type_notificacoes and not isinstance(type_notificacoes, list):
            type_notificacoes = [type_notificacoes, ]

        return self.get_notificacoes(result, type_notificacoes)
