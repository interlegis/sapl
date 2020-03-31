import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import TemplateView

from sapl.base.models import Autor
from sapl.crud.base import CrudAux
from sapl.parlamentares.models import Parlamentar
from sapl.videoconf.models import Videoconferencia

VideoConferenciaCrud = CrudAux.build(Videoconferencia, 'videoconferencia')


class ChatView(PermissionRequiredMixin, TemplateView):
    template_name = "videoconf/videoconferencia.html"
    permission_required = ('sessao.add_sessao', )
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['object'] = Videoconferencia.objects.get(id=kwargs['pk'])
        except ObjectDoesNotExist:
            pass #TODO: return error

        user = self.request.user
        content_type = ContentType.objects.get_for_model(Parlamentar)
        try:
            autor = user.autor
            nome = autor.nome
            parlamentar = None
            if not autor.object_id or autor.content_type != content_type:
                is_parlamentar = False
            else:
                try:
                    parlamentar = Parlamentar.objects.get(id=autor.object_id)
                    nome = parlamentar.nome_parlamentar
                    is_parlamentar = True
                except ObjectDoesNotExist:
                    is_parlamentar = False

            user_data = {
                'nome': nome,
                'is_autor': True,
                'is_parlamentar': is_parlamentar,
                'parlamentar': parlamentar
            }
        except:
            user_data = {
                'nome': user.username,
                'is_autor': False,
                'is_parlamentar': False
            }
        context.update(user_data)
        return context
