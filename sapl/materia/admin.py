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


    class RestricaoAdmin(admin.ModelAdmin):

        def has_add_permission(self, request, obj=None):
            return False

        def has_change_permission(self, request, obj=None):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


    admin.site.register(Proposicao, RestricaoAdmin)
    admin.site.register(TipoAutor, RestricaoAdmin)
    admin.site.register(TipoComissao, RestricaoAdmin)
    admin.site.register(TipoAfastamento, RestricaoAdmin)
    admin.site.register(SituacaoMilitar, RestricaoAdmin)
    admin.site.register(TipoDependente, RestricaoAdmin)
