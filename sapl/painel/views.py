import json

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
from sapl.crud.base import Crud
from sapl.painel.apps import AppConfig
from sapl.parlamentares.models import Legislatura, Parlamentar, Votante
from sapl.sessao.models import (ExpedienteMateria, OrdemDia, PresencaOrdemDia,
                                RegistroVotacao, SessaoPlenaria,
                                SessaoPlenariaPresenca, VotoParlamentar)
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
            msg = _('Existe mais de uma votação aberta na Sessão: ' +
                    ('''<li><a href="%s">%s</a></li>''' % (
                        reverse('sapl.sessao:sessaoplenaria_detail',
                                kwargs={'pk': votacoes_abertas.first().id}),
                        votacoes_abertas.first().__str__())) +
                    'Para votar, peça para que o Operador as feche.')
            messages.add_message(request, messages.INFO, msg)
            return None, msg

    return votacoes_abertas.first(), None


def votante_view(request):
    # Pega o votante relacionado ao usuário
    try:
        votante = Votante.objects.get(user=request.user)
    except ObjectDoesNotExist:
        raise Http404()

    context = {'head_title': str(_('Votação Individual'))}

    # Verifica se usuário possui permissão para votar
    if 'parlamentares.can_vote' in request.user.get_all_permissions():
        context.update({'permissao': True})

        # Pega sessão
        sessao, msg = votacao_aberta(request)

        if sessao and not msg:
            pk = sessao.pk
            context.update({'sessao_id': pk})
            context.update({'sessao': sessao,
                            'data': sessao.data_inicio,
                            'hora': sessao.hora_inicio})

            # Inicializa presentes
            presentes = []

            # Verifica votação aberta
            # Se aberta, verifica se é nominal. ID nominal == 2
            ordem_dia = get_materia_aberta(pk)
            expediente = get_materia_expediente_aberta(pk)

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

            if materia_aberta:
                if materia_aberta.tipo_votacao == VOTACAO_NOMINAL:
                    context.update({'materia': materia_aberta.materia,
                                    'ementa': materia_aberta.materia.ementa})

                    parlamentar = votante.parlamentar
                    parlamentar_presente = False
                    if parlamentar.id in presentes:
                        parlamentar_presente = True
                    else:
                        context.update({'error_message':
                                        'Não há presentes na Sessão com a '
                                        'matéria em votação.'})

                    if parlamentar_presente:
                        voto = []
                        if ordem_dia:
                            voto = VotoParlamentar.objects.filter(
                                ordem=ordem_dia)
                        elif expediente:
                            voto = VotoParlamentar.objects.filter(
                                expediente=expediente)

                        if voto:
                            try:
                                voto = voto.get(parlamentar=parlamentar)
                                context.update({'voto_parlamentar': voto.voto})
                            except ObjectDoesNotExist:
                                context.update(
                                    {'voto_parlamentar': 'Voto não '
                                     'computado.'})
                    else:
                        context.update({'error_message':
                                        'Você não está presente na '
                                        'Ordem do Dia/Expediente em votação.'})
                else:
                    context.update(
                        {'error_message': 'A matéria aberta não é do tipo '
                         'votação nominal.'})
            else:
                context.update(
                    {'error_message': 'Não há nenhuma matéria aberta.'})

        elif not sessao and msg:
            return HttpResponseRedirect('/')

        else:
            context.update(
                {'error_message': 'Não há nenhuma sessão com matéria aberta.'})

    else:
        context.update({'permissao': False,
                        'error_message': 'Usuário sem permissão para votar.'})

    # Salva o voto
    if request.method == 'POST':
        if ordem_dia:
            try:
                voto = VotoParlamentar.objects.get(
                    parlamentar=parlamentar,
                    ordem=ordem_dia)
            except ObjectDoesNotExist:
                voto = VotoParlamentar.objects.create(
                    parlamentar=parlamentar,
                    voto=request.POST['voto'],
                    user=request.user,
                    ip=get_client_ip(request),
                    ordem=ordem_dia)
            else:
                voto.voto = request.POST['voto']
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

        elif expediente:
            try:
                voto = VotoParlamentar.objects.get(
                    parlamentar=parlamentar,
                    expediente=expediente)
            except ObjectDoesNotExist:
                voto = VotoParlamentar.objects.create(
                    parlamentar=parlamentar,
                    voto=request.POST['voto'],
                    user=request.user,
                    ip=get_client_ip(request),
                    expediente=expediente)
            else:
                voto.voto = request.POST['voto']
                voto.ip = get_client_ip(request)
                voto.user = request.user
                voto.save()

        return HttpResponseRedirect(
            reverse('sapl.painel:voto_individual'))

    return render(request, 'painel/voto_nominal.html', context)


@user_passes_test(check_permission)
def painel_view(request, pk):
    context = {'head_title': str(_('Painel Plenário')), 'sessao_id': pk}
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
    try:
        cronometro = request.session[name]
    except KeyError:
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

    presentes_list = []
    for p in presentes:
        now_year = timezone.now().year
        # Recupera a legislatura vigente
        legislatura = Legislatura.objects.get(data_inicio__year__lte = now_year,
                                                 data_fim__year__gte = now_year)
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
            'observacao_materia': materia.observacao,
            'tipo_votacao': tipo_votacao,
            'materia_legislativa_texto': str(materia.materia)
        })

    presentes_list = sort_lista_chave(presentes_list, 'nome')

    response.update({
        'presentes': presentes_list,
        'num_presentes': num_presentes,
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


            for i, p in enumerate(response['presentes']):
                try:
                    if votos_parlamentares.get(parlamentar_id=p['parlamentar_id']).voto:
                        response['presentes'][i]['voto'] = 'Voto Informado'
                except ObjectDoesNotExist:
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
                    response['presentes'][i]['voto'] = votos_parlamentares.get(
                        parlamentar_id=p['parlamentar_id']).voto
                except ObjectDoesNotExist:
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

    response = {
        'sessao_plenaria': str(sessao),
        'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
        'sessao_plenaria_hora_inicio': sessao.hora_inicio,
        'cronometro_aparte': get_cronometro_status(request, 'aparte'),
        'cronometro_discurso': get_cronometro_status(request, 'discurso'),
        'cronometro_ordem': get_cronometro_status(request, 'ordem'),
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
