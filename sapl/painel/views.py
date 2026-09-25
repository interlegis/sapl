import html
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import (login_required, permission_required,
                                            user_passes_test)
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.base.models import CasaLegislativa
from sapl.crud.base import Crud
from sapl.painel.apps import AppConfig
from sapl.parlamentares.models import Legislatura, Parlamentar, Votante
from sapl.sessao.models import (ExpedienteMateria, OradorExpediente, OrdemDia,
                                PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca,
                                VotoParlamentar, RegistroLeitura)
from sapl.utils import filiacao_data, get_client_ip, sort_lista_chave

from .models import Cronometro

VOTACAO_NOMINAL = 2

CronometroPainelCrud = Crud.build(Cronometro, '')

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


def votacao(context, context_vars):
    logger = logging.getLogger(__name__)
    parlamentar = context_vars['votante'].parlamentar

    if parlamentar.id not in context_vars['presentes']:
        logger.error("Parlamentar com id={} não está presente na "
                     "Ordem do Dia/Expediente em votação.".format(parlamentar.id))
        context.update({'error_message':
                            'Você não está presente na '
                            'Ordem do Dia/Expediente em votação.'})
        return context, context_vars

    context_vars.update({'parlamentar': parlamentar})

    if context_vars['ordem_dia']:
        voto = VotoParlamentar.objects.filter(
            ordem=context_vars['ordem_dia'], parlamentar=parlamentar).first()
    elif context_vars['expediente']:
        voto = VotoParlamentar.objects.filter(
            expediente=context_vars['expediente'], parlamentar=parlamentar).first()
    else:
        voto = None

    if voto:
        context.update({
            'voto_parlamentar': voto.voto,
            'status_message': 'Voto registrado. Aguardando o encerramento '
                              'da votação pela Mesa.',
        })
    else:
        context.update({'status_message': 'Aguardando seu voto.'})

    return context, context_vars


@never_cache
@user_passes_test(check_permission)
def painel_view(request, pk):
    logger = logging.getLogger(__name__)

    utc_now = timezone.now()
    local_now = timezone.localtime(utc_now)
    utc_offset = int(local_now.utcoffset().total_seconds() / 60)
    server_epoch_ms = int(utc_now.timestamp() * 1000)

    logger.info(
        "painel_view pk=%s utc_now=%s local_now=%s utc_offset=%s server_epoch_ms=%s",
        pk, utc_now, local_now, utc_offset, server_epoch_ms
    )

    context = {'head_title': str(_('Painel Plenário')),
               'sessao_id': pk,
               'server_epoch_ms': server_epoch_ms,
               'utc_offset': utc_offset,
               }
    return render(request, 'painel/index.html', context)


def sessao_votacao(context, context_vars):
    pk = context_vars['sessao'].pk
    context.update({'sessao_id': pk})
    context.update({'sessao': context_vars['sessao'],
                    'data': context_vars['sessao'].data_inicio,
                    'hora': context_vars['sessao'].hora_inicio})

    # Inicializa presentes
    presentes = []
    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)
    errors_msgs = {'materia': 'Não há nenhuma matéria aberta.',
                   'registro': 'A Mesa encerrou o recebimento de novos votos '
                              'para apurar o resultado desta matéria. '
                              'Aguarde a próxima matéria.',
                   'tipo': 'Esta matéria não é votada individualmente pelos '
                          'tablets — a Mesa registra o resultado diretamente.'}

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
                         'expediente': expediente,
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
    context_vars.update({'sessao': sessao})
    if sessao and not msg:
        context, context_vars = sessao_votacao(context, context_vars)
    elif msg:
        # Mais de uma votação aberta ao mesmo tempo (não deveria acontecer
        # mais, dado o invariante garantido em abrir_votacao(), mas se
        # acontecer é preferível mostrar isso explicitamente ao vereador do
        # que redirecioná-lo silenciosamente para "/".
        context.update({'error_message': msg})
    else:
        context.update(
            {'error_message': 'Não há nenhuma sessão com matéria aberta.'})
    return context, context_vars


def _resolve_votante_context(request):
    """
    Resolve o estado atual de votação para o Votante autenticado — usado
    tanto por votante_view (renderização completa) quanto por
    votante_status (endpoint leve de polling), para as duas views
    compartilharem a mesma lógica de can_vote() em vez de duplicá-la.
    """
    username = request.user.username
    if not Votante.objects.filter(user=request.user).exists():
        logging.getLogger(__name__).warning(
            f'user={username} sem cadastro de Votante tentou acessar /voto-individual/.'
        )
        raise PermissionDenied

    context = {'head_title': str(_('Votação Individual'))}
    context_vars = {'votante': Votante.objects.get(user=request.user)}
    return can_vote(context, context_vars, request)


@never_cache
@login_required
@permission_required('parlamentares.can_vote', raise_exception=True)
def votante_status(request):
    """
    Endpoint leve para o polling automático do tablet (voto_individual.html)
    — devolve só o suficiente pra decidir se algo mudou desde o último
    carregamento da página, sem o custo de renderizar a página inteira a
    cada poll. Não reaproveita get_dados_painel: aquele endpoint exige a
    permissão do módulo painel (check_permission), que uma conta só-Votante
    não necessariamente tem.
    """
    context, context_vars = _resolve_votante_context(request)
    materia = context.get('materia')
    return JsonResponse({
        'materia_id': materia.id if materia else None,
        'error_message': context.get('error_message'),
        'status_message': context.get('status_message'),
        'voto_parlamentar': context.get('voto_parlamentar'),
    })


@never_cache
@login_required
@permission_required('parlamentares.can_vote', raise_exception=True)
def votante_view(request):
    logger = logging.getLogger(__name__)
    username = request.user.username

    template_name = 'painel/voto_individual.html'
    context, context_vars = _resolve_votante_context(request)

    # Salva o voto
    if request.method == 'POST':
        voto_submetido = request.POST.get('voto')
        votos_validos = ('Sim', 'Não', 'Abstenção')
        ordem = context_vars.get('ordem_dia')
        expediente = context_vars.get('expediente')
        parlamentar = context_vars.get('parlamentar')

        if voto_submetido not in votos_validos:
            messages.error(request, _('Voto inválido.'))
        elif parlamentar and (ordem or expediente):
            try:
                with transaction.atomic():
                    if ordem:
                        materia = OrdemDia.objects.select_for_update().get(pk=ordem.pk)
                        fase_sessao = {'ordem': materia}
                    else:
                        materia = ExpedienteMateria.objects.select_for_update().get(
                            pk=expediente.pk)
                        fase_sessao = {'expediente': materia}

                    presenca_model = (PresencaOrdemDia if ordem
                                      else SessaoPlenariaPresenca)
                    esta_presente = presenca_model.objects.filter(
                        sessao_plenaria_id=materia.sessao_plenaria_id,
                        parlamentar=parlamentar).exists()

                    if (not esta_presente or not materia.votacao_aberta or
                            materia.registro_aberto or
                            materia.tipo_votacao != VOTACAO_NOMINAL or
                            RegistroVotacao.objects.filter(**fase_sessao).exists()):
                        messages.error(
                            request,
                            _('A votação não está mais disponível para novos votos.'))
                    else:
                        try:
                            with transaction.atomic():
                                voto, created = (VotoParlamentar.objects
                                                 .select_for_update().get_or_create(
                                                     parlamentar=parlamentar,
                                                     **fase_sessao))
                        except IntegrityError:
                            voto = VotoParlamentar.objects.select_for_update().get(
                                parlamentar=parlamentar, **fase_sessao)

                        voto.voto = voto_submetido
                        voto.ip = get_client_ip(request)
                        voto.user = request.user
                        voto.save()
                        logger.info(
                            "user=%s. VotoParlamentar para parlamentar=%s "
                            "salvo com sucesso.", username, parlamentar)
            except IntegrityError:
                logger.exception(
                    "user=%s. Falha de integridade ao salvar voto de parlamentar=%s.",
                    username, parlamentar)
                messages.error(request, _('Não foi possível registrar o voto. Tente novamente.'))
        else:
            messages.error(
                request, _('A votação não está disponível para novos votos.'))

        return HttpResponseRedirect(
            reverse('sapl.painel:voto_individual'))

    return render(request, template_name, context)


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
    resposta = JsonResponse(dict(status=status))
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


@user_passes_test(check_permission)
def cronometro_painel(request):
    request.session[request.GET['tipo']] = request.GET['action']
    return HttpResponse({})


def get_cronometro_status(request, name):
    logger = logging.getLogger(__name__)
    username = request.user.username
    try:
        logger.debug("user=" + username + ". Tentando obter cronometro.")
        cronometro = request.session[name]
    except KeyError as e:
        logger.error("user=" + username + ". Erro ao obter cronometro. Retornado como vazio. " + str(e))
        cronometro = ''
    return cronometro


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
        elif materia.tipo_votacao == 4:
            tipo_votacao = 'Leitura'

        response.update({
            'tipo_resultado': materia.resultado,
            'observacao_materia': html.unescape(materia.observacao),
            'tipo_votacao': tipo_votacao,
            'materia_legislativa_texto': str(materia.materia),
            'materia_legislativa_ementa': str(materia.materia.ementa)
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


def get_votos(response, materia, mostrar_voto):
    logger = logging.getLogger(__name__)
    if type(materia) == OrdemDia:
        if materia.tipo_votacao != 4:
            registro = RegistroVotacao.objects.filter(
                ordem=materia, materia=materia.materia).order_by('data_hora').last()
            leitura = None
        else:
            leitura = RegistroLeitura.objects.filter(
                ordem=materia, materia=materia.materia).order_by('data_hora').last()
            registro = None
        tipo = 'ordem'
    elif type(materia) == ExpedienteMateria:
        if materia.tipo_votacao != 4:
            registro = RegistroVotacao.objects.filter(
                expediente=materia, materia=materia.materia).order_by('data_hora').last()
            leitura = None
        else:
            leitura = RegistroLeitura.objects.filter(
                expediente=materia, materia=materia.materia).order_by('data_hora').last()
            registro = None
        tipo = 'expediente'

    if not registro and not leitura:
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

            for i, p in enumerate(response['presentes']):
                try:
                    logger.info("Tentando obter votos do parlamentar (id={}).".format(p['parlamentar_id']))
                    voto = votos_parlamentares.get(parlamentar_id=p['parlamentar_id']).voto

                    if voto:
                        if mostrar_voto:
                            response['presentes'][i]['voto'] = voto
                        else:
                            response['presentes'][i]['voto'] = 'Voto Informado'
                except ObjectDoesNotExist:
                    # logger.error("Votos do parlamentar (id={}) não encontrados. Retornado vazio."
                    #              .format(p['parlamentar_id']))
                    response['presentes'][i]['voto'] = ''
    elif leitura:
        response.update({
            'numero_votos_sim': 0,
            'numero_votos_nao': 0,
            'numero_abstencoes': 0,
            'registro': True,
            'total_votos': 0,
            'tipo_resultado': 'Matéria lida.',
        })
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
                    logger.error(
                        "Votos do parlamentar (id={}) não encontrados. Retornado None.".format(p['parlamentar_id']))
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


@never_cache
@user_passes_test(check_permission)
def get_dados_painel(request, pk):
    sessao = SessaoPlenaria.objects.get(id=pk)

    casa = CasaLegislativa.objects.first()

    app_config = ConfiguracoesAplicacao.objects.first()

    brasao = None
    if casa and app_config and (bool(casa.logotipo)):
        brasao = casa.logotipo.url \
            if app_config.mostrar_brasao_painel else None

    response = {
        'sessao_plenaria': str(sessao),
        'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
        'sessao_plenaria_hora_inicio': sessao.hora_inicio,
        'sessao_solene': sessao.tipo.nome == "Solene",
        'sessao_finalizada': sessao.finalizada,
        'tema_solene': sessao.tema_solene,
        'cronometro_aparte': get_cronometro_status(request, 'aparte'),
        'cronometro_discurso': get_cronometro_status(request, 'discurso'),
        'cronometro_ordem': get_cronometro_status(request, 'ordem'),
        'cronometro_consideracoes': get_cronometro_status(request, 'consideracoes'),
        'status_painel': sessao.painel_aberto,
        'brasao': brasao,
        'mostrar_voto': app_config.mostrar_voto
    }

    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)

    # Caso tenha alguma matéria com votação aberta, ela é mostrada no painel
    # com prioridade para Ordem do Dia.
    if ordem_dia:
        return JsonResponse(get_votos(
            get_presentes(pk, response, ordem_dia),
            ordem_dia, app_config.mostrar_voto))
    elif expediente:
        return JsonResponse(get_votos(
            get_presentes(pk, response, expediente),
            expediente, app_config.mostrar_voto))

    # Caso não tenha nenhuma aberta,
    # a matéria a ser mostrada no Painel deve ser a última votada
    last_ordem_voto = RegistroVotacao.objects.filter(
        ordem__sessao_plenaria=sessao).order_by('data_hora').last()
    last_expediente_voto = RegistroVotacao.objects.filter(
        expediente__sessao_plenaria=sessao).order_by('data_hora').last()

    last_ordem_leitura = RegistroLeitura.objects.filter(
        ordem__sessao_plenaria=sessao).order_by('data_hora').last()
    last_expediente_leitura = RegistroLeitura.objects.filter(
        expediente__sessao_plenaria=sessao).order_by('data_hora').last()

    # Obtém última matéria que foi votada, através do timestamp mais recente
    ordem_expediente = None
    ultimo_timestamp = None
    if last_ordem_voto:
        ordem_expediente = last_ordem_voto.ordem
        ultimo_timestamp = last_ordem_voto.data_hora
    if (last_expediente_voto and ultimo_timestamp and last_expediente_voto.data_hora > ultimo_timestamp) or \
            (not ultimo_timestamp and last_expediente_voto):
        ordem_expediente = last_expediente_voto.expediente
        ultimo_timestamp = last_expediente_voto.data_hora
    if (last_ordem_leitura and ultimo_timestamp and last_ordem_leitura.data_hora > ultimo_timestamp) or \
            (not ultimo_timestamp and last_ordem_leitura):
        ordem_expediente = last_ordem_leitura.ordem
        ultimo_timestamp = last_ordem_leitura.data_hora
    if (last_expediente_leitura and ultimo_timestamp and last_expediente_leitura.data_hora > ultimo_timestamp) or \
            (not ultimo_timestamp and last_expediente_leitura):
        ordem_expediente = last_expediente_leitura.expediente
        ultimo_timestamp = last_expediente_leitura.data_hora

    if ordem_expediente:
        return JsonResponse(get_votos(
            get_presentes(pk, response, ordem_expediente),
            ordem_expediente, app_config.mostrar_voto))

    # Retorna que não há nenhuma matéria já votada ou aberta
    return response_nenhuma_materia(get_presentes(pk, response, None))
