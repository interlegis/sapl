from datetime import datetime
from re import sub

from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin
from vanilla.views import GenericView

from compilacao.views import IntegracaoTaView
from crud import Crud
from materia.models import MateriaLegislativa, TipoMateriaLegislativa

from .forms import NormaJuridicaForm
from .models import (AssuntoNorma, LegislacaoCitada, NormaJuridica,
                     TipoNormaJuridica)

assunto_norma_crud = Crud(AssuntoNorma, 'assunto_norma_juridica')
tipo_norma_crud = Crud(TipoNormaJuridica, 'tipo_norma_juridica')
norma_crud = Crud(NormaJuridica, '')
norma_temporario_crud = Crud(NormaJuridica, 'normajuridica')
legislacao_citada_crud = Crud(LegislacaoCitada, '')


class NormaIncluirView(FormMixin, GenericView):
    template_name = "norma/normajuridica_incluir.html"

    def get_success_url(self):
        return '/norma/'

    def get(self, request, *args, **kwargs):
        form = NormaJuridicaForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = NormaJuridicaForm(request.POST or None)
        if form.is_valid():
            norma = form.save(commit=False)

            if form.cleaned_data['tipo_materia']:
                tipo = TipoMateriaLegislativa.objects.get(
                    id=form.cleaned_data['tipo_materia'])
                try:
                    materia = MateriaLegislativa.objects.get(
                        tipo=tipo,
                        numero=form.cleaned_data['numero'],
                        ano=form.cleaned_data['ano'])
                except ObjectDoesNotExist:
                    return self.render_to_response(
                        {'form': form,
                         'error': 'Matéria adicionada não existe!'})
                else:
                    norma.materia = materia

            if form.cleaned_data['indexacao']:
                norma.indexacao = sub(
                    '&nbsp;', ' ', strip_tags(form.cleaned_data['indexacao']))

            if form.cleaned_data['observacao']:
                norma.observacao = sub(
                    '&nbsp;', ' ', strip_tags(form.cleaned_data['observacao']))

            if 'texto_integral' in request.FILES:
                norma.texto_integral = request.FILES['texto_integral']

            norma.ementa = sub(
                '&nbsp;', ' ', strip_tags(form.cleaned_data['ementa']))
            norma.timestamp = datetime.now()
            norma.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class NormaTaView(IntegracaoTaView):
    model = NormaJuridica
    model_type_foreignkey = TipoNormaJuridica
