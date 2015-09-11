from django.views.generic.list import ListView

from compilacao.models import Dispositivo
from norma.models import NormaJuridica


class CompilacaoView(ListView):
    model = Dispositivo
    template_name = 'compilacao/index.html'

    flag_alteradora = None

    def get_queryset(self):
        return Dispositivo.objects.filter(
            ordem__gt=0,
            norma_id=self.kwargs['norma_id']).select_related()

    def get_norma(self):
        return NormaJuridica.objects.get(
            pk=self.kwargs['norma_id'])

    def is_norma_alteradora(self):
        if self.flag_alteradora is None:
            self.flag_alteradora = NormaJuridica.objects.get(
                pk=self.kwargs['norma_id']
            ).dispositivos_alterados_set.count() > 1
        return self.flag_alteradora
