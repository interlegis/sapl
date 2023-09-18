from django.contrib import admin
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import AuditLog
from sapl.utils import register_all_models_in_admin

register_all_models_in_admin(__name__)

admin.site.site_title = 'Administração - SAPL'
admin.site.site_header = 'Administração - SAPL'


class AuditLogAdmin(admin.ModelAdmin):
    pass

    def has_add_permission(self, request):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return False
    #
    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


# Na linha acima register_all_models_in_admin registrou AuditLog
admin.site.unregister(AuditLog)
admin.site.register(AuditLog, AuditLogAdmin)
