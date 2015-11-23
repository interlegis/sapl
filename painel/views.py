from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from painel.models import Painel
from parlamentares.models import Filiacao
from sapl.crud import build_crud
from sessao.models import (OrdemDia, PresencaOrdemDia, RegistroVotacao,
                           SessaoPlenaria, SessaoPlenariaPresenca,
                           VotoParlamentar)

from .models import Cronometro

#                           VotoParlamentar)


cronometro_painel_crud = build_crud(
    Cronometro, '', [

        [_('Cronometro'),
         [('status', 3), ('data_cronometro', 6),
          ('tipo', 3)]],
    ])


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


def cronometro_painel(request):
    print(request.POST)

    return HttpResponse({})


def painel_view(request, pk):
    print(pk)
    context = {'head_title': 'Painel Plenário', 'sessao_id': pk}
    return render(request, 'painel/index.html', {'context': context})


def painel_mensagem_view(request):
    return render(request, 'painel/mensagem.html')


def painel_parlamentares_view(request):
    return render(request, 'painel/parlamentares.html')


def painel_votacao_view(request):
    return render(request, 'painel/votacao.html')


def get_dados_painel(request, pk):
    # Sessão Plenária
    sessao_plenaria_id = pk
    sessao_plenaria = SessaoPlenaria.objects.get(id=sessao_plenaria_id)

    # # Pra recuperar o partido do parlamentar
    # # tem que fazer OUTRA query, deve ter uma
    # # forma de fazer isso na base do join de data models.
    filiacao = Filiacao.objects.filter(
        data_desfiliacao__isnull=True, parlamentar__ativo=True)
    parlamentar_partido = {}
    for f in filiacao:
        parlamentar_partido[f.parlamentar.nome_parlamentar] = f.partido.sigla

    # Presença Sessão Plenária
    sessao_plenaria_presenca = SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria_id=sessao_plenaria_id)
    print(sessao_plenaria_presenca)
    presentes_sessao_plenaria = [
        p.parlamentar.nome_parlamentar for p in sessao_plenaria_presenca]
    num_presentes_sessao_plen = len(presentes_sessao_plenaria)

    # Presença Ordem do dia
    presenca_ordem_dia = PresencaOrdemDia.objects.filter(
        sessao_plenaria_id=sessao_plenaria_id)
    presentes_ordem_dia = []
    for p in presenca_ordem_dia:
        nome_parlamentar = p.parlamentar.nome_parlamentar
        presentes_ordem_dia.append(
            {'id': p.id,
             'nome': nome_parlamentar,
             'partido': parlamentar_partido[nome_parlamentar],
             })
    num_presentes_ordem_dia = len(presentes_ordem_dia)

    try:

        ordemdia = OrdemDia.objects.get(
            sessao_plenaria_id=sessao_plenaria_id, votacao_aberta=True)
        votacao_aberta = True
        materia_legislativa_texto = ordemdia.materia.ementa
        materia_observacao = ordemdia.materia.observacao
        tipo_votacao = ordemdia.tipo_votacao
        # materia_titulo = ordemdia.materia
        materia_titulo = ""

        try:
            votacao = RegistroVotacao.objects.get(
                ordem_id=ordemdia.id, materia_id=ordemdia.materia.id)
            numero_votos_sim = votacao.numero_votos_sim
            numero_votos_nao = votacao.numero_votos_nao
            numero_abstencoes = votacao.numero_abstencoes
            tipo_resultado = votacao.tipo_resultado_votacao.nome
            votacao_id = votacao.id
        except ObjectDoesNotExist:
            votacao_id = -1
            numero_votos_sim = 0
            numero_votos_nao = 0
            numero_abstencoes = 0
            tipo_resultado = ""

        total_votos = numero_votos_sim + numero_votos_nao + numero_abstencoes

        votos = {}
        try:
            voto_parlamentar = VotoParlamentar.objects.filter(
                votacao_id=votacao_id)
            for vp in voto_parlamentar:
                votos[vp.parlamentar.id] = vp.voto
        except ObjectDoesNotExist:
            pass

    except ObjectDoesNotExist:
        votacao_aberta = False
        materia_titulo = ""
        materia_legislativa_texto = ""
        materia_observacao = ""
        tipo_votacao = ""

    votacao_json = {"sessao_plenaria": str(sessao_plenaria),
                    "sessao_plenaria_data": sessao_plenaria.data_inicio,
                    "sessao_plenaria_hora_inicio": sessao_plenaria.hora_inicio,
                    "materia_titulo": materia_titulo,
                    "materia_legislativa_texto": materia_legislativa_texto,
                    "materia_observacao": materia_observacao,
                    "tipo_votacao": tipo_votacao,
                    "presentes_ordem_dia": presentes_ordem_dia,
                    "num_presentes_ordem_dia": num_presentes_ordem_dia,
                    "presentes_sessao_plenaria": presentes_sessao_plenaria,
                    "num_presentes_sessao_plenaria": num_presentes_sessao_plen,
                    "votacao_aberta": votacao_aberta,
                    "numero_votos_sim": numero_votos_sim,
                    "numero_votos_nao": numero_votos_nao,
                    "numero_abstencoes": numero_abstencoes,
                    "total_votos": total_votos,
                    "tipo_resultado": tipo_resultado,
                    "votos": votos,
                    }

    return JsonResponse(votacao_json)
