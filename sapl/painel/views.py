import html
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.base.models import CasaLegislativa
from sapl.crud.base import Crud, CrudAux
from sapl.painel.apps import AppConfig
from sapl.parlamentares.models import Legislatura, Parlamentar, Votante
from sapl.sessao.models import (ExpedienteMateria, OradorExpediente, OrdemDia,
                                PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca,
                                VotoParlamentar)
from sapl.utils import filiacao_data, get_client_ip, sort_lista_chave

from .forms import CronometroForm, ConfiguracoesPainelForm
from .models import Cronometro, PainelConfig

VOTACAO_NOMINAL = 2

class CronometroPainelCrud(CrudAux):
    model = Cronometro

    class BaseMixin(CrudAux.BaseMixin):
        form_class = CronometroForm


class PainelConfigCrud(CrudAux):
    model = PainelConfig

    class BaseMixin(CrudAux.BaseMixin):
        form_class = ConfiguracoesPainelForm
        list_url = ''
        create_url = ''

    class CreateView(CrudAux.CreateView):

        def get(self, request, *args, **kwargs):
            painel_config = PainelConfig.objects.first()

            if not painel_config:
                painel_config = PainelConfig()
                painel_config.save()

            return HttpResponseRedirect(
                reverse('sapl.painel:painelconfig_update',
                        kwargs={'pk': painel_config.pk}))

        def post(self, request, *args, **kwargs):
            return self.get(request, *args, **kwargs)

    class ListView(CrudAux.ListView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.painel:painelconfig_create'))

    class DetailView(CrudAux.DetailView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.painel:painelconfig_create'))

    class DeleteView(CrudAux.DeleteView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.painel:painelconfig_create'))


# FIXME mudar lógica


def check_permission(user):
    return user.has_module_perms(AppConfig.label)


def votacao_aberta(request):
    '''
    Função que verifica se há somente 1 uma matéria aberta ou
    nenhuma. É utilizada como uma função auxiliar para a view
    votante_view.
    '''
    logger = logging.getLogger(__name__)
    username = request.user.username

    votacoes_abertas = SessaoPlenaria.objects.filter(
        Q(ordemdia__votacao_aberta=True) |
        Q(expedientemateria__votacao_aberta=True)).distinct()

    if len(votacoes_abertas) > 1:
        msg_abertas = []
        for v in votacoes_abertas:
            msg_abertas.append('''<li><a href="%s">%s</a></li>''' % (
                reverse('sapl.sessao:sessaoplenaria_detail',
                        kwargs={'pk': v.id}),
                v.__str__()))
        logger.info('user=' + username + '. Existe mais de uma votações aberta. Elas se encontram '
                    'nas seguintes Sessões: ' + ', '.join(msg_abertas) + '. '
                    'Para votar, peça para que o Operador feche-as.')
        msg = _('Existe mais de uma votações aberta. Elas se encontram '
                'nas seguintes Sessões: ' + ', '.join(msg_abertas) + '. '
                'Para votar, peça para que o Operador feche-as.')
        messages.add_message(request, messages.INFO, msg)
        return None, msg

    elif len(votacoes_abertas) == 1:
        ordens = OrdemDia.objects.filter(
            sessao_plenaria=votacoes_abertas.first(),
            votacao_aberta=True)
        expedientes = ExpedienteMateria.objects.filter(
            sessao_plenaria=votacoes_abertas.first(),
            votacao_aberta=True)

        numero_materias_abertas = len(ordens) + len(expedientes)
        if numero_materias_abertas > 1:
            logger.info('user=' + username + '. Existe mais de uma votação aberta na Sessão: ' +
                        ('''<li><a href="%s">%s</a></li>''' % (
                        reverse('sapl.sessao:sessaoplenaria_detail',
                                kwargs={'pk': votacoes_abertas.first().id}),
                        votacoes_abertas.first().__str__())))
            msg = _('Existe mais de uma votação aberta na Sessão: ' +
                    ('''<li><a href="%s">%s</a></li>''' % (
                        reverse('sapl.sessao:sessaoplenaria_detail',
                                kwargs={'pk': votacoes_abertas.first().id}),
                        votacoes_abertas.first().__str__())) +
                    'Para votar, peça para que o Operador as feche.')
            messages.add_message(request, messages.INFO, msg)
            return None, msg

    return votacoes_abertas.first(), None


def votacao(context,context_vars):
    logger = logging.getLogger(__name__)
    parlamentar = context_vars['votante'].parlamentar
    parlamentar_presente = False
    if parlamentar.id in context_vars['presentes']:
        parlamentar_presente = True
        context_vars.update({'parlamentar': parlamentar})
    else:
        context.update({'error_message':
                        'Não há presentes na Sessão com a '
                        'matéria em votação.'})

    if parlamentar_presente:
        voto = []
        if context_vars['ordem_dia']:
            voto = VotoParlamentar.objects.filter(
                ordem=context_vars['ordem_dia'])
        elif context_vars['expediente']:
            voto = VotoParlamentar.objects.filter(
                expediente=context_vars['expediente'])

        if voto:
            try:
                logger.debug("Tentando obter objeto VotoParlamentar com parlamentar={}.".format(context_vars['parlamentar']))
                voto = voto.get(parlamentar=context_vars['parlamentar'])
                context.update({'voto_parlamentar': voto.voto})
            except ObjectDoesNotExist:
                logger.error("Voto do parlamentar {} não computado.".format(context_vars['parlamentar']))
                context.update(
                    {'voto_parlamentar': 'Voto não '
                     'computado.'})
    else:
        logger.error("Parlamentar com id={} não está presente na "
                    "Ordem do Dia/Expediente em votação.".format(parlamentar.id))
        context.update({'error_message':
                        'Você não está presente na '
                        'Ordem do Dia/Expediente em votação.'})
    return context, context_vars

def sessao_votacao(context,context_vars):
    pk = context_vars['sessao'].pk
    context.update({'sessao_id': pk})
    context.update({'sessao': context_vars['sessao'],
                    'data': context_vars['sessao'].data_inicio,
                    'hora': context_vars['sessao'].hora_inicio})

    # Inicializa presentes
    presentes = []
    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)
    errors_msgs = {'materia':'Não há nenhuma matéria aberta.',
            'registro':'A votação para esta matéria já encerrou.',
            'tipo':'A matéria aberta não é do tipo votação nominal.'}

    materia_aberta = None
    if ordem_dia:
        materia_aberta = ordem_dia
        presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=pk).values_list(
            'parlamentar_id', flat=True).distinct()
    elif expediente:
        materia_aberta = expediente
        presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=pk).values_list(
            'parlamentar_id', flat=True).distinct()

    context_vars.update({'ordem_dia': ordem_dia,
                        'expediente':expediente,
                        'presentes': presentes})

    # Verifica votação aberta
    # Se aberta, verifica se é nominal. ID nominal == 2
    erro = None
    if not materia_aberta:
        erro = 'materia'
    elif materia_aberta.registro_aberto:
        erro = 'registro'
    elif materia_aberta.tipo_votacao != VOTACAO_NOMINAL:
        erro = 'tipo'

    if not erro:
        context.update({'materia': materia_aberta.materia,
                        'ementa': materia_aberta.materia.ementa})
        context, context_vars = votacao(context, context_vars)
    else:
        context.update({'error_message': errors_msgs[erro]})

    return context, context_vars


def can_vote(context, context_vars, request):
    context.update({'permissao': True})

    # Pega sessão
    sessao, msg = votacao_aberta(request)
    context_vars.update({'sessao':sessao})
    if sessao and not msg:
        context, context_vars = sessao_votacao(context, context_vars)
    elif not sessao and msg:
        return HttpResponseRedirect('/')
    else:
        context.update(
            {'error_message': 'Não há nenhuma sessão com matéria aberta.'})
    return context, context_vars


def votante_view(request):
    logger = logging.getLogger(__name__)
    username = request.user.username

    # Pega o votante relacionado ao usuário
    template_name = 'painel/voto_nominal.html'
    context = {}
    context_vars = {}

    try:
        logger.debug('user=' + username + '. Tentando obter objeto Votante com user={}.'.format(request.user))
        votante = Votante.objects.get(user=request.user)
    except ObjectDoesNotExist:
        logger.error("user=" + username + ". Usuário (user={}) não cadastrado como votante na tela de parlamentares. " 
                     "Contate a administração de sua Casa Legislativa!".format(request.user))
        msg = _("Usuário não cadastrado como votante na tela de parlamentares. Contate a administração de sua Casa Legislativa!")
        context.update({
            'error_message':msg
        })

        return render(request, template_name, context)
    context_vars = {'votante': votante}
    context = {'head_title': str(_('Votação Individual'))}

    # Verifica se usuário possui permissão para votar
    if 'parlamentares.can_vote' in request.user.get_all_permissions():
        context, context_vars = can_vote(context, context_vars, request)
        logger.debug("user=" + username + ". Verificando se usuário {} possui permissão para votar.".format(request.user))
    else:
        logger.error("user=" + username + ". Usuário {} sem permissão para votar.".format(request.user))
        context.update({'permissao': False,
                        'error_message': 'Usuário sem permissão para votar.'})

    # Salva o voto
    if request.method == 'POST':
        if context_vars['ordem_dia']:
            try:
                logger.info("user=" + username + ". Tentando obter objeto VotoParlamentar para parlamentar={} e ordem={}."
                            .format(context_vars['parlamentar'], context_vars['ordem_dia']))
                voto = VotoParlamentar.objects.get(
                    parlamentar=context_vars['parlamentar'],
                    ordem=context_vars['ordem_dia'])
            except ObjectDoesNotExist:
                logger.error("user=" + username + ". Erro ao obter VotoParlamentar para parlamentar={} e ordem={}. Criando objeto."
                             .format(context_vars['parlamentar'], context_vars['ordem_dia']))
                voto = VotoParlamentar.objects.create(
                    parlamentar=context_vars['parlamentar'],
                    voto=request.POST['voto'],
                    user=request.user,
                    ip=get_client_ip(request),
                    ordem=context_vars['ordem_dia'])
            else:
                logger.info("user=" + username + ". VotoParlamentar para parlamentar={} e ordem={} obtido com sucesso."
                            .format(context_vars['parlamentar'], context_vars['ordem_dia']))
                voto.voto = request.POST['voto']
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

        elif context_vars['expediente']:
            try:
                logger.info("user=" + username + ". Tentando obter objeto VotoParlamentar para parlamentar={} e expediente={}."
                            .format(context_vars['parlamentar'], context_vars['expediente']))
                voto = VotoParlamentar.objects.get(
                    parlamentar=context_vars['parlamentar'],
                    expediente=context_vars['expediente'])
            except ObjectDoesNotExist:
                logger.error("user=" + username + ". Erro ao obter VotoParlamentar para parlamentar={} e expediente={}. Criando objeto."
                             .format(context_vars['parlamentar'], context_vars['expediente']))
                voto = VotoParlamentar.objects.create(
                    parlamentar=context_vars['parlamentar'],
                    voto=request.POST['voto'],
                    user=request.user,
                    ip=get_client_ip(request),
                    expediente=context_vars['expediente'])
            else:
                logger.info("user=" + username + ". VotoParlamentar para parlamentar={} e expediente={} obtido com sucesso."
                            .format(context_vars['parlamentar'], context_vars['expediente']))
                voto.voto = request.POST['voto']
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

        return HttpResponseRedirect(
            reverse('sapl.painel:voto_individual'))

    return render(request, template_name, context)


@user_passes_test(check_permission)
def painel_view(request, pk):
    exibicao = {
        'parlamentares': True,
        'oradores': True,
        'cronometros': True,
        'resultado': True,
        'materia': True
    }
    context = {'head_title': str(_('Painel Plenário')), 
               'sessao_id': pk, 
               'cronometros': Cronometro.objects.filter(ativo=True).order_by('ordenacao'),
               'painel_config': PainelConfig.objects.first(),
               'casa': CasaLegislativa.objects.last(),
               'exibicao': exibicao
               }
    return render(request, 'painel/index.html', context)

def bit_is_set(number, bit):
    return (number & (1 << bit)) != 0

@user_passes_test(check_permission)
def painel_parcial_view(request, pk, opcoes):
    opcoes = int(opcoes)
    exibicao = {
        'parlamentares': bit_is_set(opcoes,0),
        'oradores': bit_is_set(opcoes,1),
        'cronometros': bit_is_set(opcoes, 2),
        'resultado': bit_is_set(opcoes, 3),
        'materia': bit_is_set(opcoes, 4)
    }
    context = {'head_title': str(_('Painel Plenário')), 
               'sessao_id': pk, 
               'cronometros': Cronometro.objects.filter(ativo=True).order_by('ordenacao'),
               'painel_config': PainelConfig.objects.first(),
               'casa': CasaLegislativa.objects.last(),
               'exibicao': exibicao
               }
    return render(request, 'painel/index.html', context)


@user_passes_test(check_permission)
def switch_painel(request):
    sessao = SessaoPlenaria.objects.get(id=request.POST['pk_sessao'])
    switch = json.loads(request.POST['aberto'])

    if switch:
        sessao.painel_aberto = True
    else:
        sessao.painel_aberto = False

    sessao.save()
    return JsonResponse({})


@user_passes_test(check_permission)
def verifica_painel(request):
    sessao = SessaoPlenaria.objects.get(id=request.GET['pk_sessao'])
    status = sessao.painel_aberto

    CRONOMETRO_STATUS = {
        'I': 'start',
        'R': 'reset',
        'S': 'stop',
        'C': 'increment'
    }

    dict_status_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'status'))

    for key, value in dict_status_cronometros.items():
        dict_status_cronometros[key] = CRONOMETRO_STATUS[dict_status_cronometros[key]]
    
    dict_duracao_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'duracao_cronometro'))
    
    for key, value in dict_duracao_cronometros.items():
        dict_duracao_cronometros[key] = value.seconds

    resposta = JsonResponse(dict(status=status, 
                                 cronometros=dict_status_cronometros, 
                                 duracao_cronometros=dict_duracao_cronometros)
                            )
    return resposta


@user_passes_test(check_permission)
def painel_mensagem_view(request):
    return render(request, 'painel/mensagem.html')


@user_passes_test(check_permission)
def painel_parlamentar_view(request):
    return render(request, 'painel/parlamentares.html')


@user_passes_test(check_permission)
def painel_votacao_view(request):
    return render(request, 'painel/votacao.html')


CRONOMETRO_STATUS = {
        'start': 'I',
        'reset': 'R',
        'stop': 'S',
        'increment': 'C'
}

@user_passes_test(check_permission)
def cronometro_painel(request):
    acao = request.GET['action']
    cronometro_id = request.GET['tipo'].split('cronometro_')[1]
    cronometro = Cronometro.objects.get(id=cronometro_id)
    cronometro.status = CRONOMETRO_STATUS[acao]
    cronometro.ultima_alteracao_status = timezone.now()
    # Caso não seja stop, last_time virá como 0
    cronometro.last_stop_duration = request.GET.get('last_time')
    cronometro.save()
    return HttpResponse({})


def get_materia_aberta(pk):
    return OrdemDia.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def get_presentes(pk, response, materia):
    if type(materia) == OrdemDia:
        presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=pk)
    else:
        presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=pk)

    sessao = SessaoPlenaria.objects.get(id=pk)
    num_presentes = len(presentes)
    data_sessao = sessao.data_inicio
    oradores = OradorExpediente.objects.filter(
        sessao_plenaria_id=pk).order_by('numero_ordem')

    oradores_list = []
    for o in oradores:

        oradores_list.append(
            {
                'nome': o.parlamentar.nome_parlamentar,
                'numero': o.numero_ordem
            })

    presentes_list = []
    for p in presentes:
        legislatura = sessao.legislatura
        # Recupera os mandatos daquele parlamentar
        mandatos = p.parlamentar.mandato_set.filter(legislatura=legislatura)

        if p.parlamentar.ativo and mandatos:
            filiacao = filiacao_data(p.parlamentar, data_sessao, data_sessao)
            if not filiacao:
                partido = 'Sem Registro'
            else:
                partido = filiacao

            presentes_list.append(
                {'id': p.id,
                 'parlamentar_id': p.parlamentar.id,
                 'nome': p.parlamentar.nome_parlamentar,
                 'partido': partido,
                 'voto': ''
                 })

        elif not p.parlamentar.ativo or not mandatos:
            num_presentes += -1

    if materia:
        if materia.tipo_votacao == 1:
            tipo_votacao = 'Simbólica'
        elif materia.tipo_votacao == 2:
            tipo_votacao = 'Nominal'
        elif materia.tipo_votacao == 3:
            tipo_votacao = 'Secreta'

        response.update({
            'tipo_resultado': materia.resultado,
            'observacao_materia': html.unescape(materia.observacao),
            'tipo_votacao': tipo_votacao,
            'materia_legislativa_texto': str(materia.materia)
        })

    presentes_list = sort_lista_chave(presentes_list, 'nome')

    response.update({
        'presentes': presentes_list,
        'num_presentes': num_presentes,
        'oradores': oradores_list,
        'msg_painel': str(_('Votação aberta!')),
    })

    return response


def get_materia_expediente_aberta(pk):
    return ExpedienteMateria.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def response_nenhuma_materia(response):
    response.update({
        'msg_painel': str(_('Nenhuma matéria disponivel para votação.'))})
    return JsonResponse(response)


def get_votos(response, materia):
    logger = logging.getLogger(__name__)
    if type(materia) == OrdemDia:
        registro = RegistroVotacao.objects.filter(
            ordem=materia, materia=materia.materia).last()
        tipo = 'ordem'
    elif type(materia) == ExpedienteMateria:
        registro = RegistroVotacao.objects.filter(
            expediente=materia, materia=materia.materia).last()
        tipo = 'expediente'

    if not registro:
        response.update({
            'numero_votos_sim': 0,
            'numero_votos_nao': 0,
            'numero_abstencoes': 0,
            'registro': None,
            'total_votos': 0,
            'tipo_resultado': 'Ainda não foi votada.',
        })

        if materia.tipo_votacao == 2:
            if tipo == 'ordem':
                votos_parlamentares = VotoParlamentar.objects.filter(
                    ordem_id=materia.id).order_by(
                        'parlamentar__nome_parlamentar')
            else:
                votos_parlamentares = VotoParlamentar.objects.filter(
                    expediente_id=materia.id).order_by(
                        'parlamentar__nome_parlamentar')
            
            if PainelConfig.attr('mostrar_votos_antecedencia'):
                response['numero_votos_sim'] = votos_parlamentares.filter(voto="Sim").count()
                response['numero_votos_nao'] = votos_parlamentares.filter(voto="Não").count()
                response['numero_abstencoes'] = votos_parlamentares.filter(voto="Abstenção").count()
                response['total_votos'] = response['numero_votos_sim'] + response['numero_votos_nao'] + \
                                          response['numero_abstencoes']

            for i, p in enumerate(response['presentes']):
                try:
                    logger.info("Tentando obter votos do parlamentar (id={}).".format(p['parlamentar_id']))
                    vot_parl = votos_parlamentares.get(parlamentar_id=p['parlamentar_id']).voto
                    if vot_parl:
                        response['presentes'][i]['voto'] = vot_parl
                    else:
                        response['presentes'][i]['voto'] = ''
                except ObjectDoesNotExist:
                    logger.error("Votos do parlamentar (id={}) não encontrados. Retornado vazio."
                                 .format(p['parlamentar_id']))
                    response['presentes'][i]['voto'] = ''

    else:
        total = (registro.numero_votos_sim +
                 registro.numero_votos_nao +
                 registro.numero_abstencoes)

        if materia.tipo_votacao == 2:
            votos_parlamentares = VotoParlamentar.objects.filter(
                votacao_id=registro.id).order_by(
                    'parlamentar__nome_parlamentar')

            for i, p in enumerate(response['presentes']):
                try:
                    logger.debug("Tentando obter votos do parlamentar (id={}).".format(p['parlamentar_id']))
                    response['presentes'][i]['voto'] = votos_parlamentares.get(
                        parlamentar_id=p['parlamentar_id']).voto
                except ObjectDoesNotExist:
                    logger.error("Votos do parlamentar (id={}) não encontrados. Retornado None.".format(p['parlamentar_id']))
                    response['presentes'][i]['voto'] = None

        response.update({
            'numero_votos_sim': registro.numero_votos_sim,
            'numero_votos_nao': registro.numero_votos_nao,
            'numero_abstencoes': registro.numero_abstencoes,
            'registro': True,
            'total_votos': total,
            'tipo_resultado': registro.tipo_resultado_votacao.nome,
        })

    return response


@user_passes_test(check_permission)
def get_dados_painel(request, pk):
    sessao = SessaoPlenaria.objects.get(id=pk)

    casa = CasaLegislativa.objects.first()

    app_config = ConfiguracoesAplicacao.objects.first()

    brasao = None
    if casa and app_config and (bool(casa.logotipo)):
        brasao = casa.logotipo.url \
            if app_config.mostrar_brasao_painel else None
    
    CRONOMETRO_STATUS = {
        'I': 'start',
        'R': 'reset',
        'S': 'stop',
        'C': 'increment'
    }

    dict_status_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'status'))

    for key, value in dict_status_cronometros.items():
        dict_status_cronometros[key] = CRONOMETRO_STATUS[dict_status_cronometros[key]]
    
    dict_duracao_cronometros = dict(Cronometro.objects.filter(ativo=True).order_by('ordenacao').values_list('id', 'duracao_cronometro'))
    
    for key, value in dict_duracao_cronometros.items():
        dict_duracao_cronometros[key] = value.seconds

    response = {
        'sessao_plenaria': str(sessao),
        'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
        'sessao_plenaria_hora_inicio': sessao.hora_inicio,
        'cronometros': dict_status_cronometros,
        'duracao_cronometros': dict_duracao_cronometros,
        'sessao_solene': sessao.tipo.nome == "Solene",
        'sessao_finalizada': sessao.finalizada,
        'tema_solene': sessao.tema_solene,
        'status_painel': sessao.painel_aberto,
        'brasao': brasao
    }

    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)

    # Caso tenha alguma matéria com votação aberta, ela é mostrada no painel
    # com prioridade para Ordem do Dia.
    if ordem_dia:
        return JsonResponse(get_votos(
            get_presentes(pk, response, ordem_dia),
            ordem_dia))
    elif expediente:
        return JsonResponse(get_votos(
            get_presentes(pk, response, expediente),
            expediente))

    # Caso não tenha nenhuma aberta,
    # a matéria a ser mostrada no Painel deve ser a última votada
    last_ordem_voto = RegistroVotacao.objects.filter(
        ordem__sessao_plenaria=sessao).last()
    last_expediente_voto = RegistroVotacao.objects.filter(
        expediente__sessao_plenaria=sessao).last()

    if last_ordem_voto:
        ultima_ordem_votada = last_ordem_voto.ordem
    if last_expediente_voto:
        ultimo_expediente_votado = last_expediente_voto.expediente

    if last_ordem_voto or last_expediente_voto:
        # Se alguma ordem E algum expediente já tiver sido votado...
        if last_ordem_voto and last_expediente_voto:
            materia = ultima_ordem_votada\
                if last_ordem_voto.pk >= last_expediente_voto.pk\
                else ultimo_expediente_votado

        # Caso somente um deles tenha resultado, prioriza a Ordem do Dia
        elif last_ordem_voto:
            materia = ultima_ordem_votada

        # Caso a Ordem do dia não tenha resultado, mostra o último expediente
        elif last_expediente_voto:
            materia = ultimo_expediente_votado

        return JsonResponse(get_votos(
                            get_presentes(pk, response, materia),
                            materia))

    # Retorna que não há nenhuma matéria já votada ou aberta
    return response_nenhuma_materia(get_presentes(pk, response, None))
