from django.conf import settings
from django.contrib import admin

from sapl.base.models import TipoAutor
from sapl.comissoes.models import TipoComissao
from sapl.materia.models import Proposicao
from sapl.parlamentares.models import TipoAfastamento, SituacaoMilitar, \
    TipoDependente
from sapl.utils import register_all_models_in_admin


register_all_models_in_admin(__name__)

if not settings.DEBUG:

    class RestricaoAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

    models = (
        Proposicao,
        TipoAutor,
        TipoComissao,
        TipoAfastamento,
        SituacaoMilitar,
        TipoDependente
    )

    for model in models:
        if admin.site.is_registered(model):
            admin.site.unregister(model)
        admin.site.register(model, RestricaoAdmin)
