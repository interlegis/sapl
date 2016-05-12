from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from crud.base import Crud
from painel.models import Painel
from parlamentares.models import Filiacao
from sessao.models import (ExpedienteMateria, OrdemDia, PresencaOrdemDia,
                           RegistroVotacao, SessaoPlenaria,
                           SessaoPlenariaPresenca, VotoParlamentar)

from .models import Cronometro

CronometroPainelCrud = Crud.build(Cronometro, '')


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


def painel_view(request, pk):
    context = {'head_title': _('Painel Plenário').encode('utf-8'), 'sessao_id': pk}
    return render(request, 'painel/index.html', context)


def painel_mensagem_view(request):
    return render(request, 'painel/mensagem.html')


def painel_parlamentar_view(request):
    return render(request, 'painel/parlamentares.html')


def painel_votacao_view(request):
    return render(request, 'painel/votacao.html')


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
    try:
        materia = OrdemDia.objects.filter(
            sessao_plenaria_id=pk, votacao_aberta=True).last()
        return materia
    except ObjectDoesNotExist:
        return False


def get_last_materia(pk):
    try:
        materia = OrdemDia.objects.filter(
            sessao_plenaria_id=pk).last()
        return materia
    except ObjectDoesNotExist:
        return None


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
                 'partido': 'Sem Registro',
                 })
        else:
            presentes_ordem_dia.append(
                {'id': p.id,
                 'nome': nome_parlamentar,
                 'partido': parlamentar_partido[nome_parlamentar],
                 })
    num_presentes_ordem_dia = len(presentes_ordem_dia)

    if materia.tipo_votacao == 1:
        tipo_votacao = 'Simbólica'
    elif materia.tipo_votacao == 2:
        tipo_votacao = 'Nominal'
    elif materia.tipo_votacao == 3:
        tipo_votacao = 'Secreta'

    response.update({
        'presentes_ordem_dia': presentes_ordem_dia,
        'num_presentes_ordem_dia': num_presentes_ordem_dia,
        'presentes_sessao_plenaria': presentes_sessao_plenaria,
        'num_presentes_sessao_plenaria': num_presentes_sessao_plen,
        'status_painel': 'ABERTO',
        'msg_painel': _('Votação aberta!').encode('utf-8'),
        'numero_votos_sim': 0,
        'numero_votos_nao': 0,
        'numero_abstencoes': 0,
        'total_votos': 0,
        'tipo_resultado': tipo_votacao})

    return response


# ########################EXPEDIENTE############################################


def get_materia_expediente_aberta(pk):
    try:
        materia = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=pk, votacao_aberta=True).last()
        return materia
    except ObjectDoesNotExist:
        return False


def get_last_materia_expediente(pk):
    try:
        materia = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=pk).last()
        return materia
    except ObjectDoesNotExist:
        return None


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
                 'partido': 'Sem Registro',
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
    elif materia.tipo_votacao == 2:
        tipo_votacao = 'Nominal'
    elif materia.tipo_votacao == 3:
        tipo_votacao = 'Secreta'
    response.update({
        'presentes_expediente': presentes_expediente,
        'num_presentes_expediente': num_presentes_expediente,
        'presentes_sessao_plenaria': presentes_sessao_plenaria,
        'num_presentes_sessao_plenaria': num_presentes_sessao_plen,
        'status_painel': 'ABERTO',
        'msg_painel': 'Votação aberta!',
        'numero_votos_sim': 0,
        'numero_votos_nao': 0,
        'numero_abstencoes': 0,
        'total_votos': 0,
        'tipo_resultado': tipo_votacao})

    return response


# ##########################GENERAL FUNCTIONS#############################

def response_null_materia(response):
    response.update({
        'status_painel': 'FECHADO',
        'msg_painel': _('Nenhuma matéria disponivel para votação.').encode('utf-8')
    })
    return JsonResponse(response)


def get_votos(response, materia):

    if materia.tipo_votacao == 1:
        tipo_votacao = 'Simbólica'
    elif materia.tipo_votacao == 2:
        tipo_votacao = 'Nominal'
    elif materia.tipo_votacao == 3:
        tipo_votacao = 'Secreta'

    registro = RegistroVotacao.objects.filter(
        ordem=materia, materia=materia.materia).last()
    total = (registro.numero_votos_sim +
             registro.numero_votos_nao +
             registro.numero_abstencoes)
    response.update({
        'numero_votos_sim': registro.numero_votos_sim,
        'numero_votos_nao': registro.numero_votos_nao,
        'numero_abstencoes': registro.numero_abstencoes,
        'total_votos': total,
        'tipo_votacao': tipo_votacao,
        'tipo_resultado': registro.tipo_resultado_votacao.nome
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

    registro = RegistroVotacao.objects.get(
        ordem=materia, materia=materia.materia)

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
                'partido': 'Sem Registro',
            }})
        else:
            votos.update({v.parlamentar.id: {
                'parlamentar': v.parlamentar.nome_parlamentar,
                'voto': str(v.voto),
                'partido': parlamentar_partido[v.parlamentar.nome_parlamentar]
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

    ultima_ordem = get_last_materia(pk)

    if ultima_ordem:
        if ultima_ordem.resultado:
            if ultima_ordem.tipo_votacao in [1, 3]:
                return JsonResponse(
                    get_votos(get_presentes(
                        pk, response, ultima_ordem), ultima_ordem))
            elif ultima_ordem.tipo_votacao == 2:
                return JsonResponse(
                    get_votos_nominal(get_presentes(
                        pk, response, ultima_ordem), ultima_ordem))
        else:
            return JsonResponse(get_presentes(pk, response, ultima_ordem))

    ultimo_expediente = get_last_materia_expediente(pk)

    if ultimo_expediente:
        if ultimo_expediente.resultado:
            if ultimo_expediente.tipo_votacao in [1, 3]:
                return JsonResponse(
                    get_votos(get_presentes(
                              pk, response, ultimo_expediente),
                              ultimo_expediente))
            elif ultimo_expediente.tipo_votacao == 2:
                return JsonResponse(
                    get_votos_nominal(get_presentes(
                                      pk, response, ultimo_expediente),
                                      ultimo_expediente))
        else:
            return JsonResponse(get_presentes(pk, response,
                                              ultimo_expediente))
    else:
        return response_null_materia(response)
