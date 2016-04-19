from sapl.utils import register_all_models_in_admin
from django.contrib import admin
from base.models import ProblemaMigracao

register_all_models_in_admin(__name__)

admin.site.unregister(ProblemaMigracao)


@admin.register(ProblemaMigracao)
class ProblemaMigracaoAdmin(admin.ModelAdmin):
    list_display = ["content_type", "object_id", "problema",
                    "descricao", "get_url"]

    def get_url(self, obj):
        return "<a href='%s'>%s</a>" % (obj.endereco, obj.endereco)

    get_url.short_description = "Endereco"
    get_url.allow_tags = True
