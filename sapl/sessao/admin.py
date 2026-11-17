from django.contrib import admin

from sapl.sessao.models import ExpedienteMateria, OrdemDia
from sapl.utils import register_all_models_in_admin


class NoAdminAccessModelAdmin(admin.ModelAdmin):
    """
    SAPL não usa as páginas de admin e desencoraja seu uso — e votacao_aberta/
    registro_aberto só podem ser alterados com segurança através do fluxo de
    abrir_votacao()/VotacaoNominalAbstract (sapl/sessao/views.py), que
    garante a invariante de no máximo uma matéria aberta por vez. Em vez de
    apenas tornar os campos somente-leitura, o acesso ao admin é desabilitado
    por completo para estes dois modelos.
    """

    def has_view_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(OrdemDia, NoAdminAccessModelAdmin)
admin.site.register(ExpedienteMateria, NoAdminAccessModelAdmin)

# register_all_models_in_admin já pula modelos já registrados acima
register_all_models_in_admin(__name__)
