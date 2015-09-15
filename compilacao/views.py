from django.views.generic.list import ListView

from compilacao.models import Dispositivo
from norma.models import NormaJuridica

DISPOSITIVO_SELECT_RELATED = (
    'tipo_dispositivo',
    'norma_publicada',
    'norma',
    'dispositivo_atualizador',
    'dispositivo_atualizador__dispositivo_pai',
    'dispositivo_atualizador__dispositivo_pai__norma',
    'dispositivo_atualizador__dispositivo_pai__norma__tipo',
    'dispositivo_pai')


class CompilacaoView(ListView):
    template_name = 'compilacao/index.html'

    flag_alteradora = -1

    flag_nivel_ini = 0
    flag_nivel_old = -1

    itens_de_bloco = []

    def get_queryset(self):
        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1
        self.itens_de_bloco = []

        if self.is_norma_alteradora():
            return Dispositivo.objects.filter(
                ordem__gt=0,
                norma_id=self.kwargs['norma_id'],
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        else:
            return Dispositivo.objects.filter(
                ordem__gt=0,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)

    def get_norma(self):
        return NormaJuridica.objects.select_related('tipo').get(
            pk=self.kwargs['norma_id'])

    def is_norma_alteradora(self):
        if self.flag_alteradora == -1:
            self.flag_alteradora = Dispositivo.objects.select_related(
                'dispositivos_alterados_pela_norma_set'
            ).filter(norma_id=self.kwargs['norma_id']).count()
        return self.flag_alteradora > 0


class DispositivoView(ListView):
    #template_name = 'compilacao/index.html'
    template_name = 'compilacao/template_render_bloco.html'

    flag_alteradora = None

    flag_nivel_ini = 0
    flag_nivel_old = -1

    itens_de_bloco = []

    def get_queryset(self):
        self.flag_alteradora = -1
        self.flag_nivel_ini = 0
        self.flag_nivel_old = -1
        self.itens_de_bloco = []

        try:
            bloco = Dispositivo.objects.get(pk=self.kwargs['dispositivo_id'])
        except Dispositivo.DoesNotExist:
            return []

        self.flag_nivel_old = bloco.nivel - 1
        self.flag_nivel_ini = bloco.nivel

        proximo_bloco = Dispositivo.objects.filter(
            ordem__gt=bloco.ordem,
            nivel__lte=bloco.nivel,
            norma_publicada=None,
            norma_id=self.kwargs['norma_id'])[:1]

        if proximo_bloco.count() == 0:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                norma_publicada=None,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        else:
            itens = Dispositivo.objects.filter(
                ordem__gte=bloco.ordem,
                ordem__lt=proximo_bloco[0].ordem,
                norma_publicada=None,
                norma_id=self.kwargs['norma_id']
            ).select_related(*DISPOSITIVO_SELECT_RELATED)
        return itens

    def get_norma(self):
        return NormaJuridica.objects.select_related('tipo').get(
            pk=self.kwargs['norma_id'])

    def is_norma_alteradora(self):
        if self.flag_alteradora == -1:
            self.flag_alteradora = Dispositivo.objects.select_related(
                'dispositivos_alterados_pela_norma_set'
            ).filter(norma_id=self.kwargs['norma_id']).count()
        return self.flag_alteradora > 0
