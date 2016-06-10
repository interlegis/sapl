from django.contrib import admin
from django.core.urlresolvers import reverse

from sapl.base.models import ProblemaMigracao
from sapl.utils import register_all_models_in_admin

register_all_models_in_admin(__name__)

admin.site.unregister(ProblemaMigracao)


@admin.register(ProblemaMigracao)
class ProblemaMigracaoAdmin(admin.ModelAdmin):
    list_display = ["content_type", "object_id", "nome_campo", "problema",
                    "descricao", "get_url"]

    def get_url(self, obj):

        info = (obj.content_object._meta.app_label,
                obj.content_object._meta.model_name)
        endereco = reverse('admin:%s_%s_change' % info,
                           args=(obj.content_object.pk,))
        return "<a href='%s'>%s</a>" % (endereco, endereco)

    get_url.short_description = "Endereço"
    get_url.allow_tags = True
