from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.core import serializers

import json

from parlamentares.models import Parlamentar
from sessao.models import PresencaOrdemDia

def json_view(request):

   #error when trying to retrieve
   #print(PresencaOrdemDia.objects.all())

   parlamentares = serializers.serialize('json', Parlamentar.objects.all())
   return HttpResponse(parlamentares,  content_type='application/json')

   #return JsonResponse(data) # work with python dict

def painel_view(request):
    return render(request, 'painel/index.html')

def painel_parlamentares_view(request):
    return render(request, 'painel/parlamentares.html')

def painel_votacao_view(request):
    return render(request, 'painel/votacao.html')
