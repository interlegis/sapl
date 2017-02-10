from datetime import date

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from sapl.crud.base import Crud
from sapl.painel.apps import AppConfig
from sapl.painel.models import Painel
from sapl.parlamentares.models import Filiacao, Votante
from sapl.sessao.models import (ExpedienteMateria, OrdemDia, PresencaOrdemDia,
                                RegistroVotacao, SessaoPlenaria,
                                SessaoPlenariaPresenca, VotoParlamentar)

from .models import Cronometro

CronometroPainelCrud = Crud.build(Cronometro, '')

# FIXME mudar lógica


def check_permission(user):
    return user.has_module_perms(AppConfig.label)


def votante_view(request, pk):
    context = {'head_title': str(_('Votação Individual')), 'sessao_id': pk}

    # Inicializa presentes
    presentes = []

    # Verifica votação aberta
    # Se aberta, verifica se é nominal. ID nominal == 2
    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)

    if ordem_dia:
        if ordem_dia.tipo_votacao == 2:
            context.update({'materia': ordem_dia})
            presentes = PresencaOrdemDia.objects.filter(sessao_plenaria_id=pk)
    elif expediente:
        if expediente.tipo_votacao == 2:
            context.update({'materia': expediente})
            presentes = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=pk)
    else:
        context.update(
            {'materia': 'Nenhuma matéria com votação nominal aberta.'})

    # Verifica se usuário possui permissão para votar
    if 'parlamentares.can_vote' in request.user.get_all_permissions():
        context.update({'permissao': True})
    else:
        context.update({'permissao': False})

    # Verifica se usuário está presente na sessão
    try:
        votante = Votante.objects.get(user=request.user)
    except ObjectDoesNotExist:
        context.update({'error_message':
                        'Erro ao recuperar parlamentar ligado ao usuário'})
    else:
        parlamentar = votante.parlamentar
        context.update({'presente': False})
        if len(presentes) > 0:
            for p in presentes:
                if p.parlamentar.id == parlamentar:
                    context.update({'presente': True})
                    break

    # FIXME: Verificar se usuário já votou

    return render(request, 'painel/voto_nominal.html', context)


@user_passes_test(check_permission)
def controlador_painel(request):

    painel_created = Painel.objects.get_or_create(data_painel=date.today())
    painel = painel_created[0]

    if request.method == 'POST':
        if 'start-painel' in request.POST:
            painel.aberto = True
            painel.save()
        elif 'stop-painel' in request.POST:
            painel.aberto = False
            painel.save()
        elif 'save-painel' in request.POST:
            painel.mostrar = request.POST['tipo_painel']
            painel.save()

    context = {'painel': painel, 'PAINEL_TYPES': Painel.PAINEL_TYPES}
    return render(request, 'painel/controlador.html', context)


@user_passes_test(check_permission)
def painel_view(request, pk):
    context = {'head_title': str(_('Painel Plenário')), 'sessao_id': pk}
    return render(request, 'painel/index.html', context)


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

# ##############################ORDEM DO DIA##################################


def get_materia_aberta(pk):
    return OrdemDia.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def get_presentes(pk, response, materia):
    filiacao = Filiacao.objects.filter(
        data_desfiliacao__isnull=True, parlamentar__ativo=True)
    parlamentar_partido = {}
    for f in filiacao:
        parlamentar_partido[
            f.parlamentar.nome_parlamentar] = f.partido.sigla

    sessao_plenaria_presenca = SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria_id=pk)
    presentes_sessao_plenaria = [
        p.parlamentar.nome_parlamentar for p in sessao_plenaria_presenca]
    num_presentes_sessao_plen = len(presentes_sessao_plenaria)

    presenca_ordem_dia = PresencaOrdemDia.objects.filter(
        sessao_plenaria_id=pk)
    presentes_ordem_dia = []
    for p in presenca_ordem_dia:
        nome_parlamentar = p.parlamentar.nome_parlamentar

        try:
            parlamentar_partido[nome_parlamentar]
        except KeyError:
            presentes_ordem_dia.append(
                {'id': p.id,
                 'nome': nome_parlamentar,
                 'partido': str(_('Sem Registro')),
                 })
        else:
            presentes_ordem_dia.append(
                {'id': p.id,
                 'nome': nome_parlamentar,
                 'partido': parlamentar_partido[nome_parlamentar],
                 })
    num_presentes_ordem_dia = len(presentes_ordem_dia)

    if materia.tipo_votacao == 1:
        tipo_votacao = str(_('Simbólica'))
        response = get_votos(response, materia)
    elif materia.tipo_votacao == 2:
        tipo_votacao = 'Nominal'
        response = get_votos_nominal(response, materia)
    elif materia.tipo_votacao == 3:
        tipo_votacao = 'Secreta'
        response = get_votos(response, materia)

    response.update({
        'presentes_ordem_dia': presentes_ordem_dia,
        'num_presentes_ordem_dia': num_presentes_ordem_dia,
        'presentes_sessao_plenaria': presentes_sessao_plenaria,
        'num_presentes_sessao_plenaria': num_presentes_sessao_plen,
        'status_painel': 'ABERTO',
        'msg_painel': str(_('Votação aberta!')),
        'tipo_resultado': tipo_votacao,
        'observacao_materia': materia.observacao,
        'materia_legislativa_texto': str(materia.materia)})

    return response


# ########################EXPEDIENTE############################################


def get_materia_expediente_aberta(pk):
    return ExpedienteMateria.objects.filter(
        sessao_plenaria_id=pk, votacao_aberta=True).last()


def get_presentes_expediente(pk, response, materia):
    filiacao = Filiacao.objects.filter(
        data_desfiliacao__isnull=True, parlamentar__ativo=True)
    parlamentar_partido = {}
    for f in filiacao:
        parlamentar_partido[
            f.parlamentar.nome_parlamentar] = f.partido.sigla

    sessao_plenaria_presenca = SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria_id=pk)
    presentes_sessao_plenaria = [
        p.parlamentar.nome_parlamentar for p in sessao_plenaria_presenca]
    num_presentes_sessao_plen = len(presentes_sessao_plenaria)

    presenca_expediente = SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria_id=pk)
    presentes_expediente = []
    for p in presenca_expediente:
        nome_parlamentar = p.parlamentar.nome_parlamentar

        try:
            parlamentar_partido[nome_parlamentar]
        except KeyError:
            presentes_expediente.append(
                {'id': p.id,
                 'nome': nome_parlamentar,
                 'partido': str(_('Sem Registro')),
                 })
        else:
            presentes_expediente.append(
                {'id': p.id,
                 'nome': nome_parlamentar,
                 'partido': parlamentar_partido[nome_parlamentar],
                 })
    num_presentes_expediente = len(presentes_expediente)

    if materia.tipo_votacao == 1:
        tipo_votacao = 'Simbólica'
        response = get_votos(response, materia)
    elif materia.tipo_votacao == 2:
        tipo_votacao = 'Nominal'
        response = get_votos_nominal(response, materia)
    elif materia.tipo_votacao == 3:
        tipo_votacao = 'Secreta'
        response = get_votos(response, materia)

    response.update({
        'presentes_expediente': presentes_expediente,
        'num_presentes_expediente': num_presentes_expediente,
        'presentes_sessao_plenaria': presentes_sessao_plenaria,
        'num_presentes_sessao_plenaria': num_presentes_sessao_plen,
        'status_painel': str(_('ABERTO')),
        'msg_painel': str(_('Votação aberta!')),
        'tipo_resultado': tipo_votacao,
        'observacao_materia': materia.observacao,
        'materia_legislativa_texto': str(materia.materia)})

    return response


# ##########################GENERAL FUNCTIONS#############################

def response_nenhuma_materia(response):
    response.update({
        'status_painel': 'FECHADO',
        'msg_painel': str(_('Nenhuma matéria disponivel para votação.'))})
    return JsonResponse(response)


def get_votos(response, materia):
    if materia.tipo_votacao == 1:
        tipo_votacao = 'Simbólica'
    elif materia.tipo_votacao == 2:
        tipo_votacao = 'Nominal'
    elif materia.tipo_votacao == 3:
        tipo_votacao = 'Secreta'

    if type(materia) == OrdemDia:
        registro = RegistroVotacao.objects.filter(
            ordem=materia, materia=materia.materia).last()
    else:
        registro = RegistroVotacao.objects.filter(
            expediente=materia, materia=materia.materia).last()

    if registro:
        total = (registro.numero_votos_sim +
                 registro.numero_votos_nao +
                 registro.numero_abstencoes)
        response.update({
            'numero_votos_sim': registro.numero_votos_sim,
            'numero_votos_nao': registro.numero_votos_nao,
            'numero_abstencoes': registro.numero_abstencoes,
            'total_votos': total,
            'tipo_votacao': tipo_votacao,
            'tipo_resultado': registro.tipo_resultado_votacao.nome,
        })
    else:
        response.update({
            'numero_votos_sim': 0,
            'numero_votos_nao': 0,
            'numero_abstencoes': 0,
            'total_votos': 0,
            'tipo_votacao': tipo_votacao,
            'tipo_resultado': 'Ainda não foi votada.',
        })
    return response


def get_votos_nominal(response, materia):
    votos = {}

    if materia.tipo_votacao == 1:
        tipo_votacao = 'Simbólica'
    elif materia.tipo_votacao == 2:
        tipo_votacao = 'Nominal'
    elif materia.tipo_votacao == 3:
        tipo_votacao = 'Secreta'

    if type(materia) == OrdemDia:
        registro = RegistroVotacao.objects.filter(
            ordem=materia, materia=materia.materia).last()
    else:
        registro = RegistroVotacao.objects.filter(
            expediente=materia, materia=materia.materia).last()

    if not registro:
        response.update({
            'numero_votos_sim': 0,
            'numero_votos_nao': 0,
            'numero_abstencoes': 0,
            'total_votos': 0,
            'tipo_votacao': tipo_votacao,
            'tipo_resultado': 'Não foi votado ainda',
            'votos': None
        })

    else:
        votos_parlamentares = VotoParlamentar.objects.filter(
            votacao_id=registro.id)

        filiacao = Filiacao.objects.filter(
            data_desfiliacao__isnull=True, parlamentar__ativo=True)
        parlamentar_partido = {}
        for f in filiacao:
            parlamentar_partido[
                f.parlamentar.nome_parlamentar] = f.partido.sigla

        for v in votos_parlamentares:
            try:
                parlamentar_partido[v.parlamentar.nome_parlamentar]
            except KeyError:
                votos.update({v.parlamentar.id: {
                    'parlamentar': v.parlamentar.nome_parlamentar,
                    'voto': str(v.voto),
                    'partido': str(_('Sem Registro'))
                }})
            else:
                votos.update({v.parlamentar.id: {
                    'parlamentar': v.parlamentar.nome_parlamentar,
                    'voto': str(v.voto),
                    'partido': parlamentar_partido[
                        v.parlamentar.nome_parlamentar]
                }})

        total = (registro.numero_votos_sim +
                 registro.numero_votos_nao +
                 registro.numero_abstencoes)

        response.update({
            'numero_votos_sim': registro.numero_votos_sim,
            'numero_votos_nao': registro.numero_votos_nao,
            'numero_abstencoes': registro.numero_abstencoes,
            'total_votos': total,
            'tipo_votacao': tipo_votacao,
            'tipo_resultado': registro.tipo_resultado_votacao.nome,
            'votos': votos
        })

    return response


@user_passes_test(check_permission)
def get_dados_painel(request, pk):
    sessao = SessaoPlenaria.objects.get(id=pk)
    cronometro_discurso = get_cronometro_status(request, 'discurso')
    cronometro_aparte = get_cronometro_status(request, 'aparte')
    cronometro_ordem = get_cronometro_status(request, 'ordem')

    response = {
        'sessao_plenaria': str(sessao),
        'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
        'sessao_plenaria_hora_inicio': sessao.hora_inicio,
        "cronometro_aparte": cronometro_aparte,
        "cronometro_discurso": cronometro_discurso,
        "cronometro_ordem": cronometro_ordem,
    }

    ordem_dia = get_materia_aberta(pk)
    expediente = get_materia_expediente_aberta(pk)

    if ordem_dia:
        return JsonResponse(get_presentes(pk, response, ordem_dia))
    elif expediente:
        return JsonResponse(get_presentes_expediente(pk, response, expediente))

    # Ultimo voto em ordem e ultimo voto em expediente
    last_ordem_voto = RegistroVotacao.objects.filter(
        ordem__sessao_plenaria=sessao).last()
    last_expediente_voto = RegistroVotacao.objects.filter(
        expediente__sessao_plenaria=sessao).last()

    # Ultimas materias votadas
    if last_ordem_voto:
        ultima_ordem_votada = last_ordem_voto.ordem
    if last_expediente_voto:
        ultimo_expediente_votado = last_expediente_voto.expediente

    # Caso não tenha nenhuma votação aberta
    if last_ordem_voto or last_expediente_voto:

        # Se alguma ordem E algum expediente já tiver sido votado...
        if last_ordem_voto and last_expediente_voto:
            # Verifica se o último resultado é um uma ordem do dia
            if last_ordem_voto.pk >= last_expediente_voto.pk:
                if ultima_ordem_votada.tipo_votacao in [1, 3]:
                    return JsonResponse(
                        get_votos(get_presentes(
                            pk, response, ultima_ordem_votada),
                            ultima_ordem_votada))
                elif ultima_ordem_votada.tipo_votacao == 2:
                    return JsonResponse(
                        get_votos_nominal(get_presentes(
                            pk, response, ultima_ordem_votada),
                            ultima_ordem_votada))
            # Caso não seja, verifica se é um expediente
            else:
                if ultimo_expediente_votado.tipo_votacao in [1, 3]:
                    return JsonResponse(
                        get_votos(get_presentes(
                                  pk, response, ultimo_expediente_votado),
                                  ultimo_expediente_votado))
                elif ultimo_expediente_votado.tipo_votacao == 2:
                    return JsonResponse(
                        get_votos_nominal(get_presentes(
                                          pk, response,
                                          ultimo_expediente_votado),
                                          ultimo_expediente_votado))

        # Caso somente um deles tenha resultado, prioriza a Ordem do Dia
        if last_ordem_voto:
            return JsonResponse(get_presentes(
                pk, response, ultima_ordem_votada))
        # Caso a Ordem do dia não tenha resultado, mostra o último expediente
        if last_expediente_voto:
            return JsonResponse(get_presentes(pk, response,
                                              ultimo_expediente_votado))

    # Retorna que não há nenhuma matéria já votada ou aberta
    return response_nenhuma_materia(response)
