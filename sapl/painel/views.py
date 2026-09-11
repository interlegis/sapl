import html
import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import (login_required, permission_required,
                                            user_passes_test)
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
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
                                SessaoMateriasVotacoesView, SessaoPlenaria,
                                SessaoPlenariaPresenca, SessaoPresencasView,
                                VotoParlamentar, RegistroLeitura)
from sapl.utils import get_client_ip, sort_lista_chave
from image_cropping.utils import get_backend

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
                        'ementa': materia_aberta.materia.ementa,
                        'sessao_id': materia_aberta.sessao_plenaria_id})
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
    Endpoint leve para o tablet (voto_individual.html/voto-individual v2)
    — devolve só o suficiente pra decidir se o estado pessoal do Votante
    mudou, sem o custo de renderizar a página inteira. Tem checagem de
    permissão própria (parlamentares.can_vote) em vez de check_permission
    (permissão do módulo painel), que uma conta só-Votante não
    necessariamente tem.
    """
    context, context_vars = _resolve_votante_context(request)
    materia = context.get('materia')
    return JsonResponse({
        'materia_id': materia.id if materia else None,
        'error_message': context.get('error_message'),
        'status_message': context.get('status_message'),
        'voto_parlamentar': context.get('voto_parlamentar'),
    })


def _save_voto_individual(request, context_vars):
    """
    Salva o voto do Votante autenticado — compartilhado por votante_view
    (tela legada) e votante_view_v2 (Vue), cada uma redirecionando de
    volta para a própria URL depois (por isso o redirect não mora aqui).
    """
    logger = logging.getLogger(__name__)
    username = request.user.username

    if context_vars['ordem_dia']:
        fase_sessao = {'ordem': context_vars['ordem_dia']}
    elif context_vars['expediente']:
        fase_sessao = {'expediente': context_vars['expediente']}
    else:
        fase_sessao = None

    if fase_sessao is None:
        return

    # select_for_update+atomic evita corrida com uma escrita concorrente
    # na mesma linha (ex.: o operador registrando este mesmo parlamentar
    # em lote na tela "Registrar Votação" ao mesmo tempo). Diferente do
    # formulário em lote do operador, aqui é sempre seguro aplicar o
    # valor enviado: é o próprio parlamentar atualizando o próprio voto.
    try:
        with transaction.atomic():
            voto, created = VotoParlamentar.objects.select_for_update().get_or_create(
                parlamentar=context_vars['parlamentar'], **fase_sessao)
    except IntegrityError:
        voto = VotoParlamentar.objects.select_for_update().get(
            parlamentar=context_vars['parlamentar'], **fase_sessao)

    logger.info("user=" + username + ". VotoParlamentar para parlamentar={} obtido com sucesso."
                .format(context_vars['parlamentar']))
    voto.voto = request.POST['voto']
    voto.ip = get_client_ip(request)
    voto.user = request.user
    voto.save()

    broadcast_dados_painel(request, context_vars['sessao'].id)


@never_cache
@login_required
@permission_required('parlamentares.can_vote', raise_exception=True)
def votante_view(request):
    template_name = 'painel/voto_individual.html'
    context, context_vars = _resolve_votante_context(request)

    if request.method == 'POST':
        _save_voto_individual(request, context_vars)
        return HttpResponseRedirect(
            reverse('sapl.painel:voto_individual'))

    return render(request, template_name, context)


@never_cache
@login_required
@permission_required('parlamentares.can_vote', raise_exception=True)
def votante_view_v2(request):
    context, context_vars = _resolve_votante_context(request)

    if request.method == 'POST':
        _save_voto_individual(request, context_vars)
        return HttpResponseRedirect(
            reverse('sapl.painel:voto_individual_v2'))

    return render(request, 'painel/voto_individual_v2.html', context)


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


CRONOMETRO_CACHE_KEY = 'cronometro:{}'
CRONOMETRO_CACHE_TIMEOUT = None  # não expira sozinho — só quando outro action chega


@user_passes_test(check_permission)
def cronometro_painel(request):
    """
    Estado do cronômetro (start/stop/reset de cada tipo) era guardado em
    request.session — visível só para quem clicou, nunca para os outros
    clientes olhando o mesmo painel (o telão público, outros operadores).
    Agora fica em cache compartilhado, e dispara um broadcast pro grupo da
    sessão atualmente com o painel aberto, para os clientes conectados via
    WebSocket sincronizarem o cronômetro deles quase na hora — sem isso,
    dependeriam do próximo poll (até alguns segundos de atraso) para saber
    que o Presidente apertou start/stop/reset.
    """
    tipo = request.GET['tipo']
    action = request.GET['action']
    cache.set(CRONOMETRO_CACHE_KEY.format(tipo), action, CRONOMETRO_CACHE_TIMEOUT)

    sessao = SessaoPlenaria.objects.filter(painel_aberto=True).first()
    if sessao:
        broadcast_dados_painel(request, sessao.id)

    return HttpResponse({})


def get_cronometro_status(request, name):
    return cache.get(CRONOMETRO_CACHE_KEY.format(name)) or ''


def get_materia_aberta(pk):
    return OrdemDia.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def get_presentes(pk, response, materia):
    etapa_sessao = 'ordemdia' if type(materia) == OrdemDia else 'expediente'
    presencas = SessaoPresencasView.objects.filter(
        sessao_plenaria_id=pk, etapa_sessao=etapa_sessao)

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
    for p in presencas:
        presentes_list.append(
            {'id': p.id,
             'parlamentar_id': p.parlamentar_id,
             'nome': p.nome_parlamentar,
             'partido': p.filiacao,
             'voto': ''
             })

    # Fotos/crop dos parlamentares presentes — consulta em bloco, à parte do
    # loop acima, porque SessaoPresencasView é uma view flat (sem FK para
    # Parlamentar) criada para eliminar o N+1 por presente.
    fotos_by_id = {
        row['id']: row
        for row in Parlamentar.objects.filter(
            id__in=[p['parlamentar_id'] for p in presentes_list]
        ).values('id', 'fotografia', 'cropping')
    }
    for p in presentes_list:
        foto = fotos_by_id.get(p['parlamentar_id'])
        thumbnail_url = False
        if foto and foto['fotografia']:
            try:
                thumbnail_url = get_backend().get_thumbnail_url(
                    foto['fotografia'],
                    {
                        'size': (128, 128),
                        'box': foto['cropping'],
                        'crop': True,
                        'detail': True,
                    }
                )
            except Exception:
                logging.getLogger(__name__).exception(
                    'Falha ao gerar thumbnail do parlamentar id=%s.',
                    p['parlamentar_id'])
        p['fotografia'] = thumbnail_url

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
        'num_presentes': len(presentes_list),
        'oradores': oradores_list,
        'msg_painel': str(_('Votação aberta!')),
    })

    return response


def get_materia_expediente_aberta(pk):
    return ExpedienteMateria.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def get_votos(response, materia, mostrar_voto):
    etapa_sessao = 'ordemdia' if type(materia) == OrdemDia else 'expediente'
    lookup = {'ordem': materia} if type(materia) == OrdemDia else {'expediente': materia}

    if materia.tipo_votacao != 4:
        view_row = SessaoMateriasVotacoesView.objects.filter(
            id=materia.id, etapa_sessao=etapa_sessao).first()
        leitura = None
    else:
        view_row = None
        leitura = RegistroLeitura.objects.filter(
            materia=materia.materia, **lookup).order_by('data_hora').last()

    if (view_row is None or view_row.numero_votos is None) and not leitura:
        response.update({
            'numero_votos_sim': 0,
            'numero_votos_nao': 0,
            'numero_abstencoes': 0,
            'registro': None,
            'total_votos': 0,
            'tipo_resultado': 'Ainda não foi votada.',
        })

        if materia.tipo_votacao == 2:
            votos_parlamentares = (view_row.votos_parlamentares if view_row else None) or {}
            for i, p in enumerate(response['presentes']):
                voto_entry = votos_parlamentares.get(str(p['parlamentar_id']))
                voto = voto_entry['voto'] if voto_entry else None
                if voto:
                    if mostrar_voto:
                        response['presentes'][i]['voto'] = voto
                    else:
                        response['presentes'][i]['voto'] = 'Voto Informado'
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
        numero_votos = view_row.numero_votos
        votos_parlamentares = view_row.votos_parlamentares or {}

        if materia.tipo_votacao == 2:
            for i, p in enumerate(response['presentes']):
                voto_entry = votos_parlamentares.get(str(p['parlamentar_id']))
                response['presentes'][i]['voto'] = voto_entry['voto'] if voto_entry else None

        response.update({
            'numero_votos_sim': numero_votos['votos_sim'],
            'numero_votos_nao': numero_votos['votos_nao'],
            'numero_abstencoes': numero_votos['abstencoes'],
            'registro': True,
            'total_votos': numero_votos['total_votos'],
            'tipo_resultado': view_row.resultado_votacao,
        })

    return response


def build_dados_painel(request, pk):
    """
    Monta o dict completo consumido pelos broadcasts via WebSocket
    (broadcast_dados_painel() abaixo) — era também servido por um endpoint
    HTTP de polling (get_dados_painel), removido quando o polling foi
    eliminado (nenhuma tela restante lê build_dados_painel() por HTTP).
    """
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
        # Sessões anteriores à migração que introduziu este campo ficaram
        # com iniciada=None — tratado como "iniciada" (True) por
        # restringe_sessoes_visiveis() em sapl/sessao/models.py, mesma
        # convenção seguida aqui.
        'sessao_iniciada': sessao.iniciada is not False,
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
        return get_votos(
            get_presentes(pk, response, ordem_dia),
            ordem_dia, app_config.mostrar_voto)
    elif expediente:
        return get_votos(
            get_presentes(pk, response, expediente),
            expediente, app_config.mostrar_voto)

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
        return get_votos(
            get_presentes(pk, response, ordem_expediente),
            ordem_expediente, app_config.mostrar_voto)

    # Retorna que não há nenhuma matéria já votada ou aberta
    response.update({
        'msg_painel': str(_('Nenhuma matéria disponivel para votação.'))})
    return get_presentes(pk, response, None)


def broadcast_dados_painel(request, sessao_id):
    """
    Envia o estado atual da sessão para o grupo WebSocket correspondente
    (sapl/painel/consumers.py::PainelConsumer) — chamado pelas views que
    alteram voto/matéria/registro, sempre depois da escrita já ter sido
    commitada no banco. `request` é reaproveitado só para
    get_cronometro_status() dentro de build_dados_painel() (ver o item do
    cronômetro no plano — ainda lê de request.session, não de storage
    compartilhado; isso é resolvido por último, não aqui).

    Best-effort: um Redis fora do ar não pode derrubar a ação que disparou
    o broadcast (registrar voto, abrir/fechar matéria) — é exatamente por
    isso que o polling continua existindo como fallback (ver plano). Falha
    aqui só fica no log; quem está na tela sem WebSocket simplesmente
    continua vendo a atualização pelo poll de sempre.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    try:
        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            'sessao_{}'.format(sessao_id),
            {'type': 'data', 'payload': build_dados_painel(request, sessao_id)})
    except Exception:
        logging.getLogger(__name__).exception(
            'Falha ao fazer broadcast do painel para sessao_id={}.'.format(sessao_id))


# --- Vue/Pinia (v2) painel + votação nominal operator screens ---------------
#
# `controller_id` here is the sessao_plenaria id (see websocket_view's
# docstring) — kept as the parameter/URL-kwarg name to match the existing
# frontend (main.js/vue.config.js) call sites unchanged. Originally these
# four views were authored against a separate, incompatible Channels
# backend (controller_<id> groups, vote.update/stopwatch.update messages,
# a since-removed sapl.painel.consumers.get_dados_painel()); they're kept
# here with their validation/DB-write logic intact, but every broadcast now
# goes through broadcast_dados_painel() — the same full-snapshot rebroadcast
# every other painel/sessao view already uses — instead of a bespoke
# group_send. The stopwatch_controller view from that original branch is
# dropped entirely: cronometro_painel() above already does that job, keyed
# by the same discurso/aparte/ordem/consideracoes ids CronometroList.vue uses.

@never_cache
@user_passes_test(check_permission)
def websocket_view(request, controller_id):
    now = timezone.localtime(timezone.now())
    utc_offset = now.utcoffset().total_seconds() / 60
    context = {'head_title': str(_('Painel Plenário')),
               'utc_offset': utc_offset,
               'enable_live_ws': True,
               'controller_id': controller_id,  # aka, sessao_plenaria_id
               }
    return render(request, "painel/painel_v2.html", context)


VALID_VOTE_VALUES = ["Sim", "Não", "Abstenção", "Não Votou"]


@user_passes_test(check_permission)
def vote_controller(request, controller_id):
    """
    HTTP endpoint to cast/update a vote and broadcast the updated painel
    snapshot to all connected WebSocket clients.
    POST /v2/painel/controller/<sessao_id>/vote
    Body (form-encoded or JSON):
        parlamentar_id: int
        voto: str ("Sim", "Não", "Abstenção", "Não Votou")
    """
    logger = logging.getLogger(__name__)
    if request.method != 'POST':
        return JsonResponse({"type": "error", "message": "Only POST allowed"}, status=405)
    # Parse body: support both form-encoded and JSON
    if request.content_type and 'json' in request.content_type:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"type": "error", "message": "Invalid JSON"}, status=400)
        parlamentar_id = body.get("parlamentar_id")
        voto = body.get("voto")
    else:
        parlamentar_id = request.POST.get("parlamentar_id")
        voto = request.POST.get("voto")
    # Validate
    if not parlamentar_id:
        return JsonResponse({"type": "error", "message": "parlamentar_id is required"}, status=400)
    try:
        parlamentar_id = int(parlamentar_id)
    except (ValueError, TypeError):
        return JsonResponse({"type": "error", "message": "parlamentar_id must be an integer"}, status=400)
    if voto not in VALID_VOTE_VALUES:
        return JsonResponse({
            "type": "error",
            "message": f"Invalid vote value: {voto}. Must be one of: {VALID_VOTE_VALUES}"
        }, status=400)
    # Verify session exists
    try:
        SessaoPlenaria.objects.get(id=controller_id)
    except SessaoPlenaria.DoesNotExist:
        return JsonResponse({"type": "error", "message": "Session not found"}, status=404)
    # Find open materia (OrdemDia or ExpedienteMateria)
    ordem_dia = get_materia_aberta(controller_id)
    expediente = get_materia_expediente_aberta(controller_id)
    materia_aberta = ordem_dia or expediente
    if not materia_aberta:
        return JsonResponse({"type": "error", "message": "No open materia for voting"}, status=400)
    if materia_aberta.tipo_votacao != VOTACAO_NOMINAL:
        return JsonResponse({"type": "error", "message": "Materia is not nominal voting type"}, status=400)
    # Verify parlamentar exists
    try:
        parlamentar = Parlamentar.objects.get(id=parlamentar_id)
    except Parlamentar.DoesNotExist:
        return JsonResponse({"type": "error", "message": f"Parlamentar {parlamentar_id} not found"}, status=404)
    # Save/update vote
    if ordem_dia:
        voto_obj, created = VotoParlamentar.objects.update_or_create(
            parlamentar=parlamentar,
            ordem=ordem_dia,
            defaults={'voto': voto, 'user': request.user, 'ip': get_client_ip(request)}
        )
    else:
        voto_obj, created = VotoParlamentar.objects.update_or_create(
            parlamentar=parlamentar,
            expediente=expediente,
            defaults={'voto': voto, 'user': request.user, 'ip': get_client_ip(request)}
        )
    logger.info(f"Vote {'created' if created else 'updated'}: parlamentar={parlamentar_id}, voto={voto}, sessao={controller_id}")
    broadcast_dados_painel(request, controller_id)
    return JsonResponse({"ok": True, "parlamentar_id": parlamentar_id, "voto": voto, "created": created})


@user_passes_test(check_permission)
def votos_status(request, controller_id):
    """
    Estado real (não mascarado por mostrar_voto) dos votos da matéria em
    votação nominal aberta na sessão — usado pela tela de operação
    (VotacaoVotos.vue) para saber quem já votou (ex.: via tablet) sem
    correr o risco de sobrescrever um voto, sem depender do broadcast
    público do painel (build_dados_painel()/get_votos()), que mascara o
    voto individual quando app_config.mostrar_voto é False (ver
    sapl.sessao.views.VotacaoNominalAbstract._status_json, que resolve o
    mesmo problema para a tela legada — mas indexado por oid/mid, que a
    tela v2 não tem na URL; aqui o mesmo cálculo é indexado por sessao_id).
    """
    ordem_dia = get_materia_aberta(controller_id)
    expediente = get_materia_expediente_aberta(controller_id)
    materia_aberta = ordem_dia or expediente
    if not materia_aberta:
        return JsonResponse({
            "votacao_aberta": False, "registro_aberto": False,
            "ja_registrada": False, "votos": {},
        })
    lookup = {'ordem': materia_aberta} if ordem_dia else {'expediente': materia_aberta}
    votos = VotoParlamentar.objects.filter(**lookup).values_list('parlamentar_id', 'voto')
    return JsonResponse({
        "votacao_aberta": materia_aberta.votacao_aberta,
        "registro_aberto": materia_aberta.registro_aberto,
        "ja_registrada": RegistroVotacao.objects.filter(**lookup).exists(),
        "votos": {str(pid): voto for pid, voto in votos},
    })


@user_passes_test(check_permission)
def cancel_voting(request, controller_id):
    """
    HTTP endpoint to cancel the current open voting and discard all votes.
    POST /v2/painel/controller/<sessao_id>/cancel
    """
    from sapl.sessao.views import fechar_votacao_materia

    logger = logging.getLogger(__name__)

    if request.method != 'POST':
        return JsonResponse({"type": "error", "message": "Only POST allowed"}, status=405)

    # Find the open materia
    ordem_dia = get_materia_aberta(controller_id)
    expediente = get_materia_expediente_aberta(controller_id)
    materia_aberta = ordem_dia or expediente

    if not materia_aberta:
        return JsonResponse({"type": "error", "message": "No open materia for voting"}, status=400)

    # Build redirect URL before closing (materia_aberta fields change after close)
    materia_id = materia_aberta.materia_id
    if ordem_dia:
        redirect_url = reverse('sapl.sessao:ordemdia_list',
                               kwargs={'pk': controller_id}) + f'#id{materia_id}'
    else:
        redirect_url = reverse('sapl.sessao:expedientemateria_list',
                               kwargs={'pk': controller_id}) + f'#id{materia_id}'

    # Cancel: delete votes + RegistroVotacao, close materia
    fechar_votacao_materia(materia_aberta)
    logger.info(f"Voting cancelled for sessao={controller_id}, materia={materia_aberta.id}")

    broadcast_dados_painel(request, controller_id)

    return JsonResponse({"ok": True, "message": "Votação cancelada com sucesso.", "redirect_url": redirect_url})


@user_passes_test(check_permission)
def close_voting(request, controller_id):
    """
    HTTP endpoint to close the current voting and save the result.
    POST /v2/painel/controller/<sessao_id>/close
    Body (JSON):
        resultado_id: int (TipoResultadoVotacao id)
        observacoes: str (optional)
    """
    from sapl.sessao.models import TipoResultadoVotacao

    logger = logging.getLogger(__name__)

    if request.method != 'POST':
        return JsonResponse({"type": "error", "message": "Only POST allowed"}, status=405)

    # Parse body
    if request.content_type and 'json' in request.content_type:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"type": "error", "message": "Invalid JSON"}, status=400)
    else:
        body = request.POST

    resultado_id = body.get("resultado_id")
    observacoes = body.get("observacoes", "")

    if not resultado_id:
        return JsonResponse({
            "type": "error",
            "message": "Não é possível finalizar a votação sem nenhum resultado da votação"
        }, status=400)

    # Validate resultado
    try:
        tipo_resultado = TipoResultadoVotacao.objects.get(id=resultado_id)
    except TipoResultadoVotacao.DoesNotExist:
        return JsonResponse({"type": "error", "message": "Tipo de resultado não encontrado"}, status=404)

    # Find the open materia
    ordem_dia = get_materia_aberta(controller_id)
    expediente = get_materia_expediente_aberta(controller_id)
    materia_aberta = ordem_dia or expediente

    if not materia_aberta:
        return JsonResponse({"type": "error", "message": "No open materia for voting"}, status=400)

    # Count votes from VotoParlamentar
    if ordem_dia:
        votos = VotoParlamentar.objects.filter(ordem=ordem_dia)
    else:
        votos = VotoParlamentar.objects.filter(expediente=expediente)

    votos_sim = votos.filter(voto='Sim').count()
    votos_nao = votos.filter(voto='Não').count()
    abstencoes = votos.filter(voto='Abstenção').count()

    # All votes must not be "Não Votou"
    total_votados = votos_sim + votos_nao + abstencoes
    if total_votados == 0:
        return JsonResponse({
            "type": "error",
            "message": "Não é possível finalizar a votação sem nenhum voto"
        }, status=400)

    # Remove old RegistroVotacao if exists
    if ordem_dia:
        RegistroVotacao.objects.filter(ordem=ordem_dia).delete()
    else:
        RegistroVotacao.objects.filter(expediente=expediente).delete()

    # Create RegistroVotacao
    registro = RegistroVotacao()
    registro.numero_votos_sim = votos_sim
    registro.numero_votos_nao = votos_nao
    registro.numero_abstencoes = abstencoes
    registro.observacao = observacoes
    registro.user = request.user
    registro.ip = get_client_ip(request)
    registro.materia = materia_aberta.materia
    registro.tipo_resultado_votacao = tipo_resultado

    if ordem_dia:
        registro.ordem = ordem_dia
    else:
        registro.expediente = expediente

    registro.save()

    # Link VotoParlamentar records to RegistroVotacao and update user/ip
    for voto_obj in votos:
        voto_obj.votacao = registro
        voto_obj.user = request.user
        voto_obj.ip = get_client_ip(request)
        voto_obj.save()

    # Build redirect URL before closing
    materia_id = materia_aberta.materia_id
    if ordem_dia:
        redirect_url = reverse('sapl.sessao:ordemdia_list',
                               kwargs={'pk': controller_id}) + f'#id{materia_id}'
    else:
        redirect_url = reverse('sapl.sessao:expedientemateria_list',
                               kwargs={'pk': controller_id}) + f'#id{materia_id}'

    # Close materia with resultado
    materia_aberta.resultado = tipo_resultado.nome
    materia_aberta.votacao_aberta = False
    materia_aberta.save()

    # Clean up orphan VotoParlamentar (without votacao)
    if ordem_dia:
        VotoParlamentar.objects.filter(ordem=ordem_dia, votacao__isnull=True).delete()
    else:
        VotoParlamentar.objects.filter(expediente=expediente, votacao__isnull=True).delete()

    logger.info(
        f"Voting closed for sessao={controller_id}: "
        f"sim={votos_sim}, nao={votos_nao}, abstencoes={abstencoes}, "
        f"resultado={tipo_resultado.nome}"
    )

    broadcast_dados_painel(request, controller_id)

    return JsonResponse({"ok": True, "message": "Votação finalizada com sucesso.", "redirect_url": redirect_url})
