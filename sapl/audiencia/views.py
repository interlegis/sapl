import sapl

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import UpdateView
from sapl.crud.base import RP_DETAIL, RP_LIST, Crud, MasterDetailCrud

from .forms import AudienciaForm, AnexoAudienciaPublicaForm
from .models import AudienciaPublica, AnexoAudienciaPublica


def index(request):
    return HttpResponse("Audiência  Pública")


class AudienciaCrud(Crud):
    model = AudienciaPublica
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['numero', 'nome', 'tipo', 'materia',
                            'data'] 
        ordering = '-data', 'nome', 'numero', 'tipo'

    class ListView(Crud.ListView):
        paginate_by = 10

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            audiencia_materia = {}
            for o in context['object_list']:
                # indexado pelo numero da audiencia
                audiencia_materia[str(o.numero)] = o.materia

            for row in context['rows']:
                coluna_materia = row[3] # se mudar a ordem de listagem mudar aqui
                if coluna_materia[0]:
                    materia = audiencia_materia[row[0][0]]
                    url_materia = reverse('sapl.materia:materialegislativa_detail',
                                          kwargs={'pk': materia.id})
                    row[3] = (coluna_materia[0], url_materia)
            return context

    class CreateView(Crud.CreateView):
        form_class = AudienciaForm

        def form_valid(self, form):
            return super(Crud.CreateView, self).form_valid(form)

    class UpdateView(Crud.UpdateView):
        form_class = AudienciaForm

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            if self.object.materia:
                initial['tipo_materia'] = self.object.materia.tipo.id
                initial['numero_materia'] = self.object.materia.numero
                initial['ano_materia'] = self.object.materia.ano
            return initial
     
    class DeleteView(Crud.DeleteView):
        pass

    class DetailView(Crud.DetailView):

        layout_key = 'AudienciaPublicaDetail'

        @xframe_options_exempt
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)


class AudienciaPublicaMixin:

    def has_permission(self):
        app_config = sapl.base.models.AppConfig.objects.last()
        if app_config and app_config.documentos_administrativos == 'O':
            return True

        return super().has_permission()


class AnexoAudienciaPublicaCrud(MasterDetailCrud):
    model = AnexoAudienciaPublica
    parent_field = 'audiencia'
    help_topic = 'numeracao_docsacess'
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['assunto']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = AnexoAudienciaPublicaForm
        layout_key = None

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = AnexoAudienciaPublicaForm

    class ListView(AudienciaPublicaMixin, MasterDetailCrud.ListView):

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs).order_by('-data', '-id')

    class DetailView(AudienciaPublicaMixin, MasterDetailCrud.DetailView):
        pass
