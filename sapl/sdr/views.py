import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.utils import timezone

from sapl.base.models import Autor
from sapl.crud.base import Crud
from sapl.parlamentares.models import Parlamentar
from sapl.rules import RP_LIST, RP_DETAIL
from sapl.sdr.forms import DeliberacaoRemotaForm
from sapl.sdr.models import DeliberacaoRemota, gen_session_id
from sapl.sessao.models import SessaoPlenaria


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
