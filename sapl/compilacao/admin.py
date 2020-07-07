from django.contrib import admin
from sapl.compilacao.models import TipoDispositivo
from sapl.utils import register_all_models_in_admin

register_all_models_in_admin(__name__)
admin.site.unregister(TipoDispositivo)


@admin.register(TipoDispositivo)
class TipoDispositivoAdmin(admin.ModelAdmin):
    readonly_fields = ("rotulo_prefixo_texto", "rotulo_sufixo_texto",)
    list_display = [f.name for f in TipoDispositivo._meta.fields if f.name != 'id']
