import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone

from sapl.base.models import Autor
from sapl.crud.base import Crud
from sapl.parlamentares.models import Parlamentar
from sapl.rules import RP_LIST, RP_DETAIL
from sapl.sdr.forms import DeliberacaoRemotaForm
from sapl.sdr.models import DeliberacaoRemota, gen_session_id
from sapl.sessao.models import (ExpedienteMateria, OradorExpediente,
                                OradorOrdemDia, OrdemDia, PresencaOrdemDia,
                                RegistroLeitura, RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca)


class DeliberacaoRemotaCrud(Crud):
    model = DeliberacaoRemota
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        ordered_list = False
        list_field_names = [
            'titulo',
            'sessao_plenaria',
            'finalizada'
        ]

    class CreateView(Crud.CreateView):
        form_class = DeliberacaoRemotaForm
        layout_key = 'DeliberacaoRemotaCreate'
    
        def get_initial(self):
            initial = super().get_initial()
            initial['created_by'] = self.request.user
            initial['inicio'] = timezone.now()
            return initial
    
    class UpdateView(Crud.UpdateView):
        form_class = DeliberacaoRemotaForm
        layout_key = 'DeliberacaoRemotaEdit'

    class DetailView(Crud.DetailView):
        layout_key = 'DeliberacaoRemota'
        template_name = 'sdr/deliberacaoremota_detail.html'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['user'] = self.request.user

            deliberacao = DeliberacaoRemota.objects.get(pk=self.kwargs['pk'])
            context['deliberacao'] = deliberacao

            return context


#@user_passes_test(check_permission)
def get_dados_deliberacao_remota(request, pk):
    sessao = SessaoPlenaria.objects.get(id=pk)

    sessao_plenaria_presenca, oradores_expediente, materias_expediente = [], [], []
    ordemdia_presenca, oradores_ordemdia, materias_ordemdia = [], [], []

    f_od = 1 if not ExpedienteMateria.objects.filter(sessao_plenaria=sessao, votacao_aberta=True).exists() else 0
    f_em = 1 if not OrdemDia.objects.filter(sessao_plenaria=sessao, votacao_aberta=True).exists() else 0

    if f_em:
        for presenca in SessaoPlenariaPresenca.objects.filter(sessao_plenaria=sessao):
            sessao_plenaria_presenca.append(presenca.parlamentar.nome_parlamentar)

        for orador in OradorExpediente.objects.filter(sessao_plenaria=sessao).order_by("numero_ordem"):
            oradores_expediente.append(str(orador.numero_ordem) + " - " + orador.parlamentar.nome_parlamentar)

        for expediente in ExpedienteMateria.objects.filter(sessao_plenaria=sessao):
            if expediente.tipo_votacao == 4:
                if RegistroLeitura.objects.filter(expediente=expediente).exists():
                    materias_expediente.append(
                        (
                            str(expediente.numero_ordem), expediente.materia.__str__(),
                            expediente.materia.ementa, "Matéria Lida"
                        )
                    )
                else:
                    materias_expediente.append(
                        (
                            str(expediente.numero_ordem), expediente.materia.__str__(),
                            expediente.materia.ementa, "Matéria Não Lida"
                        )
                    )   
            else:
                if RegistroVotacao.objects.filter(expediente=expediente).exists():
                    registro = RegistroVotacao.objects.get(expediente=expediente)
                    materias_expediente.append(
                        (
                            str(expediente.numero_ordem), expediente.materia.__str__(),
                            expediente.materia.ementa, registro.tipo_resultado_votacao.nome
                        )
                    )
                else:
                    materias_expediente.append(
                        (
                            str(expediente.numero_ordem), expediente.materia.__str__(),
                            expediente.materia.ementa, "Matéria Não Votada"
                        )
                    )

    if f_od:
        for presenca in PresencaOrdemDia.objects.filter(sessao_plenaria=sessao):
            ordemdia_presenca.append(presenca.parlamentar.nome_parlamentar)

        for orador in OradorOrdemDia.objects.filter(sessao_plenaria=sessao).order_by("numero_ordem"):
            oradores_ordemdia.append(str(orador.numero_ordem) + " - " + orador.parlamentar.nome_parlamentar)

        for ordemdia in OrdemDia.objects.filter(sessao_plenaria=sessao):
            if ordemdia.tipo_votacao == 4:
                if RegistroLeitura.objects.filter(ordem=ordemdia).exists():
                    materias_ordemdia.append(
                        (
                            str(ordemdia.numero_ordem), ordemdia.materia.__str__(),
                            ordemdia.materia.ementa, "Matéria Lida"
                        )
                    )
                else:
                    materias_ordemdia.append(
                        (
                            str(ordemdia.numero_ordem), ordemdia.materia.__str__(),
                            ordemdia.materia.ementa, "Matéria Não Lida"
                        )
                    )   
            else:
                if RegistroVotacao.objects.filter(ordem=ordemdia).exists():
                    registro = RegistroVotacao.objects.get(ordem=ordemdia)
                    materias_ordemdia.append(
                        (
                            str(ordemdia.numero_ordem), ordemdia.materia.__str__(),
                            ordemdia.materia.ementa, registro.tipo_resultado_votacao.nome
                        )
                    )
                else:
                    materias_ordemdia.append(
                        (
                            str(ordemdia.numero_ordem), ordemdia.materia.__str__(),
                            ordemdia.materia.ementa, "Matéria Não Votada"
                        )
                    )

    response = {
        'sessao_plenaria': str(sessao), 'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
        'sessao_plenaria_hora_inicio': sessao.hora_inicio,
        'sessao_plenaria_iniciada': "Sim" if sessao.iniciada else "Não",
        'f_em': f_em, 'f_od': f_od, 'sessao_plenaria_presenca': sessao_plenaria_presenca,
        'oradores_expediente': oradores_expediente, 'materias_expediente': materias_expediente,
        'ordemdia_presenca': ordemdia_presenca, 'oradores_ordemdia': oradores_ordemdia,
        'materias_ordemdia': materias_ordemdia
    }

    return JsonResponse(response)


class ChatView(TemplateView):
# class ChatView(PermissionRequiredMixin, TemplateView):
    template_name = "sdr/deliberacaoremota.html"
    # permission_required = ('sessao.view_expedientemateria')
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['object'] = DeliberacaoRemota.objects.get(id=kwargs['pk'])
        except ObjectDoesNotExist:
            pass #TODO: return error

        user = self.request.user
        content_type = ContentType.objects.get_for_model(Parlamentar)
        try:
            autor = user.autor
            nome_usuario = autor.nome
            parlamentar = None
            if not autor.object_id or autor.content_type != content_type:
                is_parlamentar = False
            else:
                try:
                    parlamentar = Parlamentar.objects.get(id=autor.object_id)
                    nome_usuario = parlamentar.nome_parlamentar
                    is_parlamentar = True
                except ObjectDoesNotExist:
                    is_parlamentar = False

            user_data = {
                'nome_usuario': nome_usuario,
                'is_autor': True,
                'is_parlamentar': is_parlamentar,
                'parlamentar': parlamentar
            }
        except:
            user_data = {
                'nome_usuario': user.username,
                'is_autor': False,
                'is_parlamentar': False
            }

        context.update(user_data)

        return context
