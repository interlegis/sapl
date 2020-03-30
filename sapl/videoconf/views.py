from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin

# Create your views here.


class VideoConferenciaView(PermissionRequiredMixin, TemplateView):
    template_name = "videoconf/videoconferencia.html"
    permission_required = ('sessao.add_sessao', )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
