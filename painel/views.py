from datetime import date

from django.core import serializers
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

cronometro_painel_crud = build_crud(
    Cronometro, '', [

        [_('Cronometro'),
         [('status', 3), ('data_cronometro', 6),
          ('tipo', 3)]],
    ])

# REST WS


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
    context = {'head_title': 'Painel Plenário',
               'title': '3a. Sessao Ordinária do Município XYZ'}
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

    # # Ordem Dia 
    # ordem_dia = OrdemDia.objects.get(sessao_plenaria_id = sessao_plenaria_id)

    # # Pra recuperar o partido do parlamentar
    # # tem que fazer OUTRA query, deve ter uma
    # # forma de fazer isso na base do join de data models.
    filiacao = Filiacao.objects.filter(data_desfiliacao__isnull=True, parlamentar__ativo=True)
    parlamentar_partido = {}
    for f in filiacao:
        parlamentar_partido[f.parlamentar.nome_parlamentar] = f.partido.sigla   

    # Presença Sessão Plenária
    sessao_plenaria_presenca = SessaoPlenariaPresenca.objects.filter(id=sessao_plenaria_id)    
    presentes_sessao_plenaria = [p.parlamentar.nome_parlamentar for p in sessao_plenaria_presenca]
    num_presentes_sessao_plen = len(presentes_sessao_plenaria)

    # Presença Ordem do dia
    presenca_ordem_dia = PresencaOrdemDia.objects.filter(sessao_plenaria_id=sessao_plenaria_id)
    presentes_ordem_dia = []
    for p in presenca_ordem_dia:
        nome_parlamentar = p.parlamentar.nome_parlamentar
        presentes_ordem_dia.append(
            {'nome': nome_parlamentar,
             'partido': parlamentar_partido[nome_parlamentar],
             #'voto': votos.get(nome_parlamentar, '-')
             })
    num_presentes_ordem_dia = len(presentes_ordem_dia)


    # # TODO: se tentar usar objects.get(ordem_id = 104
    # # ocorre a msg: 'RegistroVotacao' object does not support indexing
    # # TODO; tratar o caso de vir vazio
    # votacao = RegistroVotacao.objects.first()

    # # Magic!
    # # http://stackoverflow.com/questions/15507171/django-filter-query-foreign-key
    # # recuperar pela votacao.id
    # voto_parlamentar = VotoParlamentar.objects.filter(votacao_id=votacao.id)
    # votos = {}
    # for vp in voto_parlamentar:
    #     votos[vp.parlamentar.nome_parlamentar] = vp.voto        

    # total_votos = votacao.numero_votos_sim + votacao.numero_votos_nao + votacao.numero_abstencoes

    # tipo_resultado = votacao.tipo_resultado_votacao.nome.upper()

    votacao_json = {"sessao_plenaria": str(sessao_plenaria),
                    "sessao_plenaria_data": sessao_plenaria.data_inicio,
                    "sessao_plenaria_hora_inicio": sessao_plenaria.hora_inicio,
                    #"materia_legislativa_texto": ordem_dia.materia.ementa,
                    #"observacao_materia": ordem_dia.materia.observacao,
                    # "tipo_votacao": ordem_dia.tipo_votacao,
                    # "numero_votos_sim": votacao.numero_votos_sim,
                    # "numero_votos_nao": votacao.numero_votos_nao,
                    # "numero_abstencoes": votacao.numero_abstencoes,
                    # "total_votos": total_votos,
                    # "presentes": presentes,
                    # "tipo_resultado": tipo_resultado,
                    "presentes_ordem_dia": presentes_ordem_dia,
                    "num_presentes_ordem_dia": num_presentes_ordem_dia,                    
                    "presentes_sessao_plenaria": presentes_sessao_plenaria,
                    "num_presentes_sessao_plenaria": num_presentes_sessao_plen,
                    }


    return JsonResponse(votacao_json)
