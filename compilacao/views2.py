from collections import OrderedDict
from datetime import datetime, timedelta
from os.path import sys

from django.core.signing import Signer
from django.db.models import Q
from django.http.response import JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView

from compilacao import forms
from compilacao.models import (Dispositivo, Nota,
                               PerfilEstruturalTextoArticulado,
                               TextoArticulado, TipoDispositivo, TipoNota,
                               TipoPublicacao, TipoVide, VeiculoPublicacao,
                               Vide)
from sapl.crud import build_crud

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

perfil_estr_txt_norm = build_crud(
    PerfilEstruturalTextoArticulado, 'perfil_estrutural', [

        [_('Perfil Estrutural de Textos Articulados'),
         [('sigla', 2), ('nome', 10)]],
    ])


veiculo_publicacao_crud = build_crud(
    VeiculoPublicacao, 'veiculo_publicacao', [

        [_('Veículo de Publicação'),
         [('sigla', 2), ('nome', 10)]],
    ])

tipo_dispositivo_crud = build_crud(
    TipoDispositivo, 'tipo_dispositivo', [

        [_('Dados Básicos'),
         [('nome', 8), ('class_css', 4)]],

        [_('Configurações para Edição do Rótulo'),
         [('rotulo_prefixo_texto', 3),
          ('rotulo_sufixo_texto', 3),
          ('rotulo_ordinal', 3),
          ('contagem_continua', 3)],

         ],

        [_('Configurações para Renderização de Rótulo e Texto'),
         [('rotulo_prefixo_html', 6),
          ('rotulo_sufixo_html', 6), ],

         [('texto_prefixo_html', 4),
          ('dispositivo_de_articulacao', 4),
          ('texto_sufixo_html', 4)],
         ],

        [_('Configurações para Nota Automática'),
         [('nota_automatica_prefixo_html', 6),
          ('nota_automatica_sufixo_html', 6),
          ],
         ],

        [_('Configurações para Variações Numéricas'),

         [('formato_variacao0', 12)],
         [('rotulo_separador_variacao01', 5), ('formato_variacao1', 7), ],
         [('rotulo_separador_variacao12', 5), ('formato_variacao2', 7), ],
         [('rotulo_separador_variacao23', 5), ('formato_variacao3', 7), ],
         [('rotulo_separador_variacao34', 5), ('formato_variacao4', 7), ],
         [('rotulo_separador_variacao45', 5), ('formato_variacao5', 7), ],

         ],

    ])


class CompilacaoView(ListView):
    template_name = 'compilacao/index.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    itens_de_vigencia = {}

    inicio_vigencia = None
    fim_vigencia = None

    def get_context_data(self, **kwargs):
        context = super(CompilacaoView, self).get_context_data(**kwargs)

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
                'dispositivo_atualizador__dispositivo_pai__ta__tipo',
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
            'ta_publicado__tipo',
            'ta__tipo',)

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
        return TextoArticulado.objects.select_related('tipo').get(
            pk=self.kwargs['ta_id'])

    def is_ta_alterador(self):
        if self.flag_alteradora == -1:
            self.flag_alteradora = Dispositivo.objects.select_related(
                'dispositivos_alterados_pelo_texto_articulado_set'
            ).filter(ta_id=self.kwargs['ta_id']).count()
        return self.flag_alteradora > 0


class DispositivoView(CompilacaoView):
    # template_name = 'compilacao/index.html'
    template_name = 'compilacao/index_bloco.html'

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


def handle_uploaded_file(f, outfilepath):
    with open(outfilepath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


class CompilacaoEditView(CompilacaoView, FormMixin):

    template_name = 'compilacao/edit.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    pk_edit = 0
    pk_view = 0

    def post(self, request, *args, **kwargs):
        form = forms.UpLoadImportFileForm(request.POST, request.FILES)
        message = "Arquivo Submetido com sucesso"

        self.object_list = self.get_queryset()

        if form.is_valid():
            try:
                f = request.FILES['import_file']
                outfilepath = '/tmp/' + f.name
                handle_uploaded_file(f, outfilepath)

                # p = Parser()
                # p.parser(outfilepath)

            except Exception as e:
                print(e)

            context = self.get_context_data(
                object_list=self.object_list,
                form=form,
                message=message,
                view=self,
                parser_list=[])
            return render(request, self.template_name, context)
        else:
            context = self.get_context_data(
                object_list=self.object_list,
                form=form,
                message=form.errors,
                view=self)
            return self.form_invalid(context)

        return self.render_to_response({'form': form})

    def form_invalid(self, context):
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):

        self.object_list = self.get_queryset()
        form_class = forms.UpLoadImportFileForm
        self.form = self.get_form(form_class)
        context = self.get_context_data(
            object_list=self.object_list,
            form=self.form)

        return self.render_to_response(context)

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
            a.inicio_vigencia = ta.data_publicacao
            a.inicio_eficacia = ta.data_publicacao
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
            e.inicio_vigencia = ta.data_publicacao
            e.inicio_eficacia = ta.data_publicacao
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


class DispositivoEditView(CompilacaoEditView):
    template_name = 'compilacao/edit_bloco.html'

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
                return self.get(request, *args, **kwargs)

            if dnext[0].nivel > d.nivel:
                pais = [d.pk, ]
            else:
                if dnext[0].dispositivo_pai_id == d.dispositivo_pai_id:
                    pais = [dnext[0].dispositivo_pai_id, ]
                else:
                    pais = [
                        dnext[0].dispositivo_pai_id, d.dispositivo_pai_id, ]
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
