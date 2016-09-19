from django.contrib import admin

from sapl.materia.models import Proposicao
from sapl.settings import DEBUG
from sapl.utils import register_all_models_in_admin

register_all_models_in_admin(__name__)

if not DEBUG:

    admin.site.unregister(Proposicao)

    class ProposicaoAdmin(admin.ModelAdmin):
        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False

    admin.site.register(Proposicao, ProposicaoAdmin)
