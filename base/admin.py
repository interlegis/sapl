from django.contrib import admin

from base.models import ProblemaMigracao
from sapl.utils import register_all_models_in_admin
from django.core.urlresolvers import reverse

register_all_models_in_admin(__name__)

admin.site.unregister(ProblemaMigracao)


@admin.register(ProblemaMigracao)
class ProblemaMigracaoAdmin(admin.ModelAdmin):
    list_display = ["content_type", "object_id", "problema",
                    "descricao", "get_url"]

    def get_url(self, obj):
        info = (obj._meta.app_label, obj._meta.model_name)
        endereco = reverse('admin:%s_%s_change' % info, args=(obj.pk,))
        return "<a href='%s'>%s</a>" % (endereco, endereco)

    get_url.short_description = "Endereço"
    get_url.allow_tags = True
