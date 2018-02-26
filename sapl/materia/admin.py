from django.contrib import admin
from sapl.materia.models import Proposicao, TipoMateriaLegislativa
from sapl.base.models import TipoAutor
from sapl.comissoes.models import TipoComissao
from sapl.parlamentares.models import TipoAfastamento, SituacaoMilitar, TipoDependente
from sapl.norma.models import TipoNormaJuridica, TipoVinculoNormaJuridica
from sapl.sessao.models import TipoSessaoPlenaria, TipoExpediente, TipoResultadoVotacao
from sapl.protocoloadm.models import TipoDocumentoAdministrativo
from sapl.settings import DEBUG
from sapl.utils import register_all_models_in_admin

register_all_models_in_admin(__name__)

if not DEBUG:

    admin.site.unregister(Proposicao)
    admin.site.unregister(TipoAutor)
    admin.site.unregister(TipoComissao)
    admin.site.unregister(TipoAfastamento)
    admin.site.unregister(SituacaoMilitar)
    admin.site.unregister(TipoDependente)
    admin.site.unregister(TipoNormaJuridica)
    admin.site.unregister(TipoVinculoNormaJuridica)
    admin.site.unregister(TipoSessaoPlenaria)
    admin.site.unregister(TipoExpediente)
    admin.site.unregister(TipoResultadoVotacao)
    admin.site.unregister(TipoDocumentoAdministrativo)
    admin.site.unregister(TipoMateriaLegislativa)

    class ProposicaoAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoAutorAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoComissaoAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoAfastamentoAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class SituacaoMilitarAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoNormaJuridicaAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoVinculoNormaJuridicaAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoDependenteAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoSessaoPlenariaAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoExpedienteAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoResultadoVotacaoAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoDocumentoAdministrativoAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    class TipoMateriaLegislativaAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False
    admin.site.register(Proposicao, ProposicaoAdmin)
    admin.site.register(TipoAutor, TipoAutorAdmin)
    admin.site.register(TipoComissao, TipoComissaoAdmin)
    admin.site.register(TipoAfastamento, TipoAfastamentoAdmin)
    admin.site.register(SituacaoMilitar, SituacaoMilitarAdmin)
    admin.site.register(TipoDependente, TipoNormaJuridicaAdmin)
    admin.site.register(TipoDependente, TipoVinculoNormaJuridicaAdmin)
    admin.site.register(TipoDependente, TipoDependenteAdmin)
    admin.site.register(TipoSessaoPlenaria, TipoSessaoPlenariaAdmin)
    admin.site.register(TipoExpediente, TipoExpedienteAdmin)
    admin.site.register(TipoResultadoVotacao, TipoResultadoVotacaoAdmin)
    admin.site.register(TipoDocumentoAdministrativo, TipoDocumentoAdministrativoAdmin)
    admin.site.register(TipoMateriaLegislativa, TipoMateriaLegislativaAdmin)
