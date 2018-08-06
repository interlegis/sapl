from rest_framework import serializers

from sapl.base.models import CasaLegislativa
from sapl.sessao.models import SessaoPlenaria, OrdemDia


class SessaoPlenariaSerializer(serializers.ModelSerializer):

    codReuniao = serializers.SerializerMethodField('get_pk_sessao')
    codReuniaoPrincipal = serializers.SerializerMethodField('get_pk_sessao')
    txtTituloReuniao = serializers.SerializerMethodField('get_name')
    txtSiglaOrgao = serializers.SerializerMethodField('get_sigla_orgao')
    txtApelido = serializers.SerializerMethodField('get_name')
    txtNomeOrgao = serializers.SerializerMethodField('get_nome_orgao')
    codEstadoReuniao = serializers.SerializerMethodField(
        'get_estadoSessaoPlenaria')
    txtTipoReuniao = serializers.SerializerMethodField('get_tipo_sessao')
    txtObjeto = serializers.SerializerMethodField('get_assunto_sessao')
    txtLocal = serializers.SerializerMethodField('get_endereco_orgao')
    bolReuniaoConjunta = serializers.SerializerMethodField(
        'get_reuniao_conjunta')
    bolHabilitarEventoInterativo = serializers.SerializerMethodField(
        'get_iterativo')
    idYoutube = serializers.SerializerMethodField('get_url')
    codEstadoTransmissaoYoutube = serializers.SerializerMethodField(
        'get_estadoTransmissaoYoutube')
    datReuniaoString = serializers.SerializerMethodField('get_date')

    # Constantes SessaoPlenaria (de 1-9) (apenas 3 serão usados)
    SESSAO_FINALIZADA = 4
    SESSAO_EM_ANDAMENTO = 3
    SESSAO_CONVOCADA = 2

    # Constantes EstadoTranmissaoYoutube (de 0 a 2)
    TRANSMISSAO_ENCERRADA = 2
    TRANSMISSAO_EM_ANDAMENTO = 1
    SEM_TRANSMISSAO = 0

    class Meta:
        model = SessaoPlenaria
        fields = (
            'codReuniao',
            'codReuniaoPrincipal',
            'txtTituloReuniao',
            'txtSiglaOrgao',
            'txtApelido',
            'txtNomeOrgao',
            'codEstadoReuniao',
            'txtTipoReuniao',
            'txtObjeto',
            'txtLocal',
            'bolReuniaoConjunta',
            'bolHabilitarEventoInterativo',
            'idYoutube',
            'codEstadoTransmissaoYoutube',
            'datReuniaoString'
        )

    def __init__(self, *args, **kwargs):
        super(SessaoPlenariaSerializer, self).__init__(args, kwargs)

    def get_pk_sessao(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.__str__()

    def get_estadoSessaoPlenaria(self, obj):
        if obj.finalizada:
            return self.SESSAO_FINALIZADA
        elif obj.iniciada:
            return self.SESSAO_EM_ANDAMENTO
        else:
            return self.SESSAO_CONVOCADA

    def get_tipo_sessao(self, obj):
        return obj.tipo.__str__()

    def get_url(self, obj):
        return obj.url_video if obj.url_video else None

    def get_iterativo(self, obj):
        return obj.interativa if obj.interativa else False

    def get_date(self, obj):
        return "{} {}{}".format(
            obj.data_inicio.strftime("%d/%m/%Y"),
            obj.hora_inicio,
            ":00"
        )

    def get_estadoTransmissaoYoutube(self, obj):
        if obj.url_video:
            if obj.finalizada:
                return self.TRANSMISSAO_ENCERRADA
            else:
                return self.TRANSMISSAO_EM_ANDAMENTO
        else:
            return self.SEM_TRANSMISSAO

    def get_assunto_sessao(self, obj):
        pauta_sessao = ''
        ordem_dia = OrdemDia.objects.filter(sessao_plenaria=obj.pk)
        pauta_sessao = ', '.join([i.materia.__str__() for i in ordem_dia])

        return str(pauta_sessao)

    def get_endereco_orgao(self, obj):
        return self.casa().endereco

    def get_reuniao_conjunta(self, obj):
        return False

    def get_sigla_orgao(self, obj):
        return self.casa().sigla

    def get_nome_orgao(self, obj):
        return self.casa().nome

    def casa(self):
        casa = CasaLegislativa.objects.first()
        return casa
