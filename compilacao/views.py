from collections import OrderedDict
from datetime import timedelta
from os.path import sys

from django.core.signing import Signer
from django.db.models import Q
from django.db.models.aggregates import Max
from django.http.response import JsonResponse
from django.utils.dateparse import parse_date
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView

from compilacao.models import Dispositivo, TipoNota, TipoVide, TipoPublicacao,\
    VeiculoPublicacao, TipoDispositivo
from norma.models import NormaJuridica
from sapl.crud import build_crud


DISPOSITIVO_SELECT_RELATED = (
    'tipo_dispositivo',
    'norma_publicada',
    'norma',
    'dispositivo_atualizador',
    'dispositivo_atualizador__dispositivo_pai',
    'dispositivo_atualizador__dispositivo_pai__norma',
    'dispositivo_atualizador__dispositivo_pai__norma__tipo',
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
                norma_id=self.kwargs['norma_id'],
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        else:
            return Dispositivo.objects.filter(
                ordem__gt=0,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)

    def get_vigencias(self):
        itens = Dispositivo.objects.filter(
            norma_id=self.kwargs['norma_id'],
        ).order_by(
            'inicio_vigencia'
        ).distinct(
            'inicio_vigencia'
        ).select_related(
            'norma_publicada',
            'norma',
            'norma_publicada__tipo',
            'norma__tipo',)

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
                ano = item.norma_publicada.ano
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

    def get_norma(self):
        return NormaJuridica.objects.select_related('tipo').get(
            pk=self.kwargs['norma_id'])

    def is_norma_alteradora(self):
        if self.flag_alteradora == -1:
            self.flag_alteradora = Dispositivo.objects.select_related(
                'dispositivos_alterados_pela_norma_set'
            ).filter(norma_id=self.kwargs['norma_id']).count()
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
            norma_id=self.kwargs['norma_id'])[:1]

        if proximo_bloco.count() == 0:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        else:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                ordem__lt=proximo_bloco[0].ordem,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        return itens


class CompilacaoEditView(CompilacaoView):
    template_name = 'compilacao/edit.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    pk_add = 0
    pk_view = 0

    def get_queryset(self):
        self.pk_add = 0
        self.pk_view = 0

        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1

        return Dispositivo.objects.filter(
            ordem__gt=0,
            norma_id=self.kwargs['norma_id']
        ).select_related(*DISPOSITIVO_SELECT_RELATED)


class DispositivoEditView(CompilacaoEditView):
    template_name = 'compilacao/edit_bloco.html'

    def get_queryset(self):
        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1

        try:
            self.pk_add = int(self.request.GET['pkadd'])
        except:
            self.pk_add = 0
        self.pk_view = int(self.kwargs['dispositivo_id'])

        try:
            if self.pk_add == self.pk_view:
                bloco = Dispositivo.objects.get(
                    pk=self.kwargs['dispositivo_id'])
            else:
                bloco = Dispositivo.objects.get(
                    pk=self.kwargs['dispositivo_id'])
        except Dispositivo.DoesNotExist:
            return []

        self.flag_nivel_old = bloco.nivel - 1
        self.flag_nivel_ini = bloco.nivel

        if self.pk_add == self.pk_view:
            return [bloco, ]

        proximo_bloco = Dispositivo.objects.filter(
            ordem__gt=bloco.ordem,
            nivel__lte=bloco.nivel,
            norma_id=self.kwargs['norma_id'])[:1]

        if proximo_bloco.count() == 0:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        else:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                ordem__lt=proximo_bloco[0].ordem,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        return itens

    def select_provaveis_inserts(self):

        # Não salvar d_base
        if self.pk_add == 0:
            d_base = Dispositivo.objects.get(pk=self.pk_view)
        else:
            d_base = Dispositivo.objects.get(pk=self.pk_add)

        result = [{'tipo_insert': 'Inserir Depois',
                   'action': 'add_next',
                   'itens': []},
                  {'tipo_insert': 'TODO: Inserir Dentro',
                   'action': 'add_in',
                   'itens': []},
                  {'tipo_insert': 'TODO: Inserir Antes',
                   'action': 'add_prior',
                   'itens': []}
                  ]

        disps = Dispositivo.objects.order_by(
            '-ordem').filter(
                ordem__lte=d_base.ordem,
                norma_id=d_base.norma_id)

        nivel = sys.maxsize
        for d in disps:

            if d.nivel >= nivel:
                continue

            if d.tipo_dispositivo.class_css == 'caput':
                continue

            nivel = d.nivel

            r = []

            if d == d_base:
                result[2]['itens'].append({
                    'class_css': d.tipo_dispositivo.class_css,
                    'tipo_pk': d.pk,
                    'variacao': 0,
                    'provavel': '%s (%s)' % (
                        d.rotulo_padrao(True, d, False),
                        d.tipo_dispositivo.nome,),
                    'dispositivo_base': d_base.pk})

            flag_direcao = 1
            flag_variacao = 0
            while True:
                # rt resultado da transformacao
                rt = d.transform_in_next(flag_direcao)
                if not rt[0]:
                    break
                flag_variacao += rt[1]
                r.append({'class_css': d.tipo_dispositivo.class_css,
                          'tipo_pk': d.tipo_dispositivo.pk,
                          'variacao': flag_variacao,
                          'provavel': '%s (%s)' % (
                              d.rotulo_padrao(
                                  True, d_base, True),
                              d.tipo_dispositivo.nome,),
                          'dispositivo_base': d_base.pk})

                flag_direcao = -1

            r.reverse()

            if len(r) > 0 and d.tipo_dispositivo.class_css == 'articulacao':
                r = [r[0], ]

            if d.tipo_dispositivo == d_base.tipo_dispositivo:
                result[0]['itens'] += r
            else:
                result[0]['itens'] += r
                result[2]['itens'] += r

            if nivel == 0:
                break

        # tipo do dispositivo base
        tipb = d_base.tipo_dispositivo

        for mudarnivel in [1, 0]:
            if mudarnivel:
                # Outros Tipos de Dispositivos PARA DENTRO
                otds = TipoDispositivo.objects.order_by(
                    '-contagem_continua', 'id').filter(
                    Q(id__gt=100) & Q(id__gt=d_base.tipo_dispositivo_id))
            else:
                # Outros Tipos de Dispositivos PARA FORA
                classes_ja_inseridas = []
                for c in result[0]['itens']:
                    if c['class_css'] not in classes_ja_inseridas:
                        classes_ja_inseridas.append(c['class_css'])
                otds = TipoDispositivo.objects.order_by(
                    '-contagem_continua', 'id').filter(
                    id__gt=100,
                    id__lt=d_base.tipo_dispositivo_id).exclude(
                        class_css__in=classes_ja_inseridas)

            for td in otds:

                if td.class_css == 'caput' or (tipb.class_css == 'caput' and
                                               td.class_css == 'paragrafo'):
                    continue

                d_base.tipo_dispositivo = td

                if td.contagem_continua:
                    disps = Dispositivo.objects.filter(
                        tipo_dispositivo_id=td.pk,
                        ordem__lte=d_base.ordem,
                        norma_id=d_base.norma_id).aggregate(
                        Max('dispositivo0'),
                        Max('dispositivo1'),
                        Max('dispositivo2'),
                        Max('dispositivo3'),
                        Max('dispositivo4'),
                        Max('dispositivo5'))

                else:
                    disps = Dispositivo.objects.filter(
                        tipo_dispositivo_id=td.pk,
                        dispositivo_pai_id=d_base.pk).aggregate(
                        Max('dispositivo0'),
                        Max('dispositivo1'),
                        Max('dispositivo2'),
                        Max('dispositivo3'),
                        Max('dispositivo4'),
                        Max('dispositivo5'))

                if disps['dispositivo0__max'] is not None:
                    d_base.set_numero_completo([
                        disps['dispositivo0__max'],
                        disps['dispositivo1__max'],
                        disps['dispositivo2__max'],
                        disps['dispositivo3__max'],
                        disps['dispositivo4__max'],
                        disps['dispositivo5__max'],
                    ])

                    d_base.transform_in_next()
                else:
                    if ';' in td.rotulo_prefixo_texto:
                        d_base.set_numero_completo([0, 0, 0, 0, 0, 0, ])
                    else:
                        d_base.set_numero_completo([1, 0, 0, 0, 0, 0, ])

                r = [{'class_css': td.class_css,
                      'tipo_pk': td.pk,
                      'variacao': 0,
                      'provavel': '%s (%s)' % (
                          d_base.rotulo_padrao(True, None, True),
                          td.nome,),
                      'dispositivo_base': d_base.pk}]

                if mudarnivel == 1:
                    result[1]['itens'] += r
                else:
                    if td.pk < tipb.pk:
                        result[2]['itens'] += r
                        result[0]['itens'] += r

        # retira inserir após e inserir antes
        if tipb.class_css == 'caput':
            result.pop()
            # result.remove(result[0])

        if tipb.class_css == 'articulacao':
            r = result[0]
            result.remove(result[0])
            result.insert(1, r)

        return result


class ActionsEditMixin(object):

    def render_to_json_response(self, context, **response_kwargs):

        if context['action'] == 'add_next':
            return JsonResponse(self.add_next(context), safe=False)
        elif context['action'] == 'add_in':
            return JsonResponse(self.add_in(context), safe=False)
        elif context['action'] == 'add_prior':
            return JsonResponse(self.add_prior(context), safe=False)
        else:
            return JsonResponse({}, safe=False)

    def add_prior(self, context):
        pass

    def add_in(self, context):
        pass

    def add_next(self, context):
        try:
            base = Dispositivo.objects.get(pk=context['dispositivo_id'])
            dp = Dispositivo.objects.get(pk=context['dispositivo_id'])

            tipo = TipoDispositivo.objects.get(pk=context['tipo_pk'])

            while dp.dispositivo_pai is not None and \
                    dp.tipo_dispositivo_id != tipo.pk:
                dp = dp.dispositivo_pai

            # Inserção interna a uma articulação um tipo já existente
            # ou de uma articulacao
            if dp.dispositivo_pai is not None or \
                    tipo.class_css == 'articulacao':

                dp.transform_in_next(int(context['variacao']))
                dp.rotulo = dp.rotulo_padrao()
                dp.texto = ''
                dp.pk = None
                dp.norma_publicada = None

                if dp.tipo_dispositivo.class_css == 'artigo':
                    ordem = base.criar_espaco_apos(espaco_a_criar=2)
                else:
                    ordem = base.criar_espaco_apos(espaco_a_criar=1)

                dp.ordem = ordem

                # Incrementar irmãos

                if not tipo.contagem_continua:
                    irmaos = list(Dispositivo.objects.filter(
                        dispositivo_pai_id=dp.dispositivo_pai_id,
                        ordem__gt=dp.ordem,
                        tipo_dispositivo_id=tipo.pk))
                elif tipo.class_css == 'articulacao':
                    irmaos = list(Dispositivo.objects.filter(
                        ordem__gt=dp.ordem,
                        norma_id=dp.norma_id,
                        tipo_dispositivo_id=tipo.pk))
                else:  # contagem continua restrita a articulacao

                    proxima_articulacao = Dispositivo.objects.filter(
                        ordem__gt=dp.ordem,
                        nivel=0,
                        norma_id=dp.norma_id)[:1]

                    if not proxima_articulacao.exists():
                        irmaos = list(Dispositivo.objects.filter(
                            ordem__gt=dp.ordem,
                            norma_id=dp.norma_id,
                            tipo_dispositivo_id=tipo.pk))
                    else:
                        irmaos = list(Dispositivo.objects.filter(
                            Q(ordem__gt=dp.ordem) &
                            Q(ordem__lt=proxima_articulacao[0].ordem),
                            norma_id=dp.norma_id,
                            tipo_dispositivo_id=tipo.pk))

                dp_profundidade = dp.get_profundidade()

                irmaos_a_salvar = []
                ultimo_irmao = None
                for irmao in irmaos:
                    irmao_profundidade = irmao.get_profundidade()
                    if irmao_profundidade < dp_profundidade:
                        break

                    if irmao.get_numero_completo() < dp.get_numero_completo():
                        if irmao_profundidade > dp_profundidade:
                            if ultimo_irmao is None:
                                irmao.transform_in_next(
                                    dp_profundidade - irmao_profundidade)
                                irmao.transform_in_next(
                                    irmao_profundidade - dp_profundidade)
                            else:
                                irmao.set_numero_completo(
                                    ultimo_irmao.get_numero_completo())

                                irmao.transform_in_next(
                                    irmao_profundidade -
                                    ultimo_irmao.get_profundidade())

                            ultimo_irmao = irmao
                        else:
                            irmao.transform_in_next()
                        irmao.rotulo = irmao.rotulo_padrao()
                        irmaos_a_salvar.append(irmao)
                    else:
                        irmao_numero = irmao.get_numero_completo()
                        irmao_numero[dp_profundidade] += 1
                        irmao.set_numero_completo(irmao_numero)
                        irmao.rotulo = irmao.rotulo_padrao()
                        irmaos_a_salvar.append(irmao)

                irmaos_a_salvar.reverse()
                for irmao in irmaos_a_salvar:
                    irmao.clean()
                    irmao.save()

                dp.clean()
                dp.save()

                # Inserção automática do caput para artigos
                if dp.tipo_dispositivo.class_css == 'artigo':
                    tipocaput = TipoDispositivo.objects.filter(
                        class_css='caput')
                    dp.dispositivo_pai_id = dp.pk
                    dp.pk = None
                    dp.nivel += 1
                    dp.tipo_dispositivo = tipocaput[0]
                    dp.set_numero_completo([1, 0, 0, 0, 0, 0, ])
                    dp.rotulo = dp.rotulo_padrao()
                    dp.texto = ''

                    dp.ordem = ordem + Dispositivo.INTERVALO_ORDEM
                    dp.clean()
                    dp.save()
                    dp = Dispositivo.objects.get(pk=dp.dispositivo_pai_id)

            # Inserção de dispositivo sem precedente de mesmo tipo
            else:
                dp = Dispositivo.objects.get(pk=context['dispositivo_id'])

                # Encontrar primeiro irmão que contem um pai compativel
                while True:
                    if dp.dispositivo_pai is not None and \
                            dp.dispositivo_pai.tipo_dispositivo_id > tipo.pk:
                        dp = dp.dispositivo_pai
                    else:
                        break

                dp.tipo_dispositivo = tipo

                dp.pk = None
                dp.norma_publicada = None

                if tipo.contagem_continua:
                    ultimo_irmao = Dispositivo.objects.order_by('-ordem').filter(
                        ordem__lte=dp.ordem,
                        tipo_dispositivo_id=tipo.pk,
                        norma_id=dp.norma_id)[:1]

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
                dp.rotulo = dp.rotulo_padrao()
                dp.texto = ''
                dp.ordem = base.criar_espaco_apos(espaco_a_criar=1)

                # Incrementar irmãos
                irmaos = Dispositivo.objects.order_by('-ordem').filter(
                    dispositivo_pai_id=dp.dispositivo_pai_id,
                    ordem__gt=dp.ordem,
                    tipo_dispositivo_id=tipo.pk)

                ''' inserção sem precedente é feita sem variação
                portanto, não deve ser usado o transform_next() para
                incrementar, e sim, apenas somar no atributo dispositivo0
                dada a possibilidade de existir irmãos com viariação'''
                for irmao in irmaos:
                    irmao.dispositivo0 += 1
                    irmao.rotulo = irmao.rotulo_padrao()
                    irmao.clean()
                    irmao.save()

                dp.clean()
                dp.save()

            ''' Reenquadrar todos os dispositivos que possuem pai
            antes da inserção atual e que são inferiores a dp,
            redirecionando para o novo pai'''

            possiveis_filhos = Dispositivo.objects.filter(
                ordem__gt=dp.ordem,
                norma_id=dp.norma_id)

            nivel = sys.maxsize
            flag_niveis = False
            for filho in possiveis_filhos:

                if filho.nivel > nivel:
                    continue

                if filho.tipo_dispositivo_id <= dp.tipo_dispositivo_id:
                    break

                if filho.dispositivo_pai.ordem >= dp.ordem:
                    continue

                nivel = filho.nivel

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
            if tipo.class_css == 'articulacao':

                proxima_articulacao = Dispositivo.objects.filter(
                    ordem__gt=dp.ordem,
                    nivel=0,
                    norma_id=dp.norma_id)[:1]

                if not proxima_articulacao.exists():
                    filhos_continuos = list(Dispositivo.objects.filter(
                        ordem__gt=dp.ordem,
                        norma_id=dp.norma_id,
                        tipo_dispositivo__contagem_continua=True))
                else:
                    filhos_continuos = list(Dispositivo.objects.filter(
                        Q(ordem__gt=dp.ordem) &
                        Q(ordem__lt=proxima_articulacao[0].ordem),
                        norma_id=dp.norma_id,
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

        # data = serializers.serialize('json',  dp)
        if tipo.contagem_continua:
            # pais a atualizar

            pais = []

            if dp.dispositivo_pai is None:
                data = {'pk': dp.pk, 'pai': [-1, ]}
            else:
                pkfilho = dp.pk
                dp = dp.dispositivo_pai

                if proxima_articulacao is not None and \
                        proxima_articulacao.exists():
                    parents = Dispositivo.objects.filter(
                        norma_id=dp.norma_id,
                        ordem__gte=dp.ordem,
                        ordem__lt=proxima_articulacao[0].ordem,
                        nivel__lte=dp.nivel)
                else:
                    parents = Dispositivo.objects.filter(
                        norma_id=dp.norma_id,
                        ordem__gte=dp.ordem,
                        nivel__lte=dp.nivel)

                nivel = sys.maxsize
                for p in parents:

                    if p.nivel > nivel:
                        continue

                    pais.append(p.pk)
                    nivel = p.nivel
                data = {'pk': pkfilho, 'pai': pais}
        else:
            data = {'pk': dp.pk, 'pai': [dp.dispositivo_pai.pk, ]}

        return data


class ActionsEditView(ActionsEditMixin, TemplateView):

    def render_to_response(self, context, **response_kwargs):
        context['action'] = self.request.GET['action']
        context['tipo_pk'] = self.request.GET['tipo_pk']
        context['variacao'] = self.request.GET['variacao']
        return self.render_to_json_response(context, **response_kwargs)
