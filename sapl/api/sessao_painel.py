"""
Leitura, em uma única requisição, de tudo o que um painel eletrônico ou
integração precisa para montar uma Sessão Plenária: sessão, mesa,
parlamentares, presenças, expediente, ordem do dia, matérias, autorias,
votações, votos, leituras e oradores. Ver docs/api-sessao-painel.md.

Cada bloco usa o mesmo serializer do endpoint de listagem do model, então
os registros têm o mesmo formato de /api/<app>/<model>/.
"""
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, prefetch_related_objects

from drfautoapi.drfautoapi import ApiViewSetConstrutor
from sapl.api.permissions import SaplModelPermissions
from sapl.base.models import Autor, CasaLegislativa, Metadata, TipoAutor
from sapl.materia.models import Autoria, MateriaLegislativa
from sapl.parlamentares.models import (CargoMesa, Filiacao, Mandato,
                                       Parlamentar, Partido)
from sapl.sessao.models import (ExpedienteMateria, ExpedienteSessao,
                                IntegranteMesa, Orador, OradorExpediente,
                                OradorOrdemDia, OrdemDia, PresencaOrdemDia,
                                RegistroLeitura, RegistroVotacao,
                                SessaoPlenariaPresenca, TipoExpediente,
                                TipoResultadoVotacao, TipoSessaoPlenaria,
                                VotoParlamentar)


def serializar(request, model, objs, many=True):
    """Serializa com o serializer da listagem do model. Metadata e campos
    many-to-many de todos os registros são lidos de uma vez, em vez de uma
    consulta por registro."""
    serializer_class = ApiViewSetConstrutor.get_viewset_for_model(
        model).serializer_class
    lista = list(objs) if many else [objs]
    prefetch_related_objects(
        lista, *(f.name for f in model._meta.many_to_many))
    content_type = ContentType.objects.get_for_model(model)
    metadata = dict.fromkeys(((model._meta.label, o.pk) for o in lista), {})
    metadata.update({
        (model._meta.label, m.object_id): m.metadata
        for m in Metadata.objects.filter(
            content_type=content_type,
            object_id__in=[o.pk for o in lista])})
    return serializer_class(
        lista if many else objs, many=many,
        context={'request': request, 'metadata': metadata}).data


def por_id(objs):
    return {o.pk: o for o in objs}


class SessaoPainel:

    # Models lidos, para conferir a permissão de leitura de cada um com as
    # mesmas regras dos endpoints de listagem.
    MODELS = (
        TipoSessaoPlenaria, CasaLegislativa, Parlamentar, Mandato, Filiacao,
        Partido, CargoMesa, IntegranteMesa, SessaoPlenariaPresenca,
        PresencaOrdemDia, TipoExpediente, ExpedienteSessao,
        ExpedienteMateria, OrdemDia, MateriaLegislativa, Autoria, Autor,
        TipoAutor, TipoResultadoVotacao, RegistroVotacao, VotoParlamentar,
        RegistroLeitura, Orador, OradorExpediente, OradorOrdemDia,
    )

    def __init__(self, sessao, request):
        self.sessao = sessao
        self.request = request

    def models_sem_permissao(self):
        permissao = SaplModelPermissions()
        sem = []
        for model in self.MODELS:
            # SaplModelPermissions confere a permissão pelo queryset da view.
            view = type('View', (), {'queryset': model.objects.none()})()
            if not permissao.has_permission(self.request, view):
                sem.append('{}.{}'.format(model._meta.app_label,
                                          model._meta.model_name))
        return sem

    def dados(self):
        """
        Os registros da sessão recebem a própria sessão já carregada, e
        votações, votos e leituras recebem os itens da pauta já carregados:
        o __str__ de cada um sobe por essas relações e, sem isso, faria
        consultas por registro.
        """
        s = self.sessao
        r = self.request

        def da_sessao(model, *relacionados):
            objs = list(model.objects.filter(
                sessao_plenaria=s).select_related(*relacionados))
            for o in objs:
                o.sessao_plenaria = s
            return objs

        ordens = da_sessao(OrdemDia, 'materia__tipo')
        expedientes_materia = da_sessao(ExpedienteMateria, 'materia__tipo')
        ordens_por_id = por_id(ordens)
        expedientes_por_id = por_id(expedientes_materia)
        da_pauta = Q(ordem_id__in=ordens_por_id) | \
            Q(expediente_id__in=expedientes_por_id)

        def na_pauta(objs):
            for o in objs:
                if o.ordem_id:
                    o.ordem = ordens_por_id[o.ordem_id]
                if o.expediente_id:
                    o.expediente = expedientes_por_id[o.expediente_id]
            return objs

        registros_votacao = na_pauta(list(RegistroVotacao.objects.filter(
            da_pauta).select_related('tipo_resultado_votacao')))
        registros_por_id = por_id(registros_votacao)
        votos = na_pauta(list(VotoParlamentar.objects.filter(
            da_pauta).select_related('parlamentar')))
        for v in votos:
            if v.votacao_id in registros_por_id:
                v.votacao = registros_por_id[v.votacao_id]
        registros_leitura = na_pauta(list(RegistroLeitura.objects.filter(
            da_pauta).select_related('materia__tipo')))

        materias_ids = {o.materia_id for o in ordens + expedientes_materia}
        materias = list(MateriaLegislativa.objects.filter(
            id__in=materias_ids).select_related('tipo'))
        autorias = list(Autoria.objects.filter(
            materia_id__in=materias_ids).select_related(
                'autor__tipo', 'materia__tipo').prefetch_related(
                    'autor__autor_related'))
        autores = {a.autor_id: a.autor for a in autorias}

        presencas = da_sessao(SessaoPlenariaPresenca, 'parlamentar')
        presencas_ordem = da_sessao(PresencaOrdemDia, 'parlamentar')
        mesa = da_sessao(IntegranteMesa, 'parlamentar', 'cargo')
        expedientes = da_sessao(ExpedienteSessao, 'tipo')
        oradores = {model: da_sessao(model, 'parlamentar')
                    for model in (Orador, OradorExpediente, OradorOrdemDia)}

        # Parlamentares com mandato na legislatura da sessão e qualquer
        # outro citado nela (presença, mesa, voto ou orador).
        mandatos = list(Mandato.objects.filter(
            legislatura_id=s.legislatura_id).select_related(
                'parlamentar', 'legislatura'))
        parlamentares_ids = {o.parlamentar_id for o in (
            mandatos + presencas + presencas_ordem + mesa + votos +
            [o for lista in oradores.values() for o in lista])}
        filiacoes = list(Filiacao.objects.filter(
            parlamentar_id__in=parlamentares_ids).select_related(
                'parlamentar', 'partido'))

        return {
            'sessao_plenaria': serializar(r, type(s), s, many=False),
            'tipo_sessao': serializar(
                r, TipoSessaoPlenaria, s.tipo, many=False),
            'casa_legislativa': serializar(
                r, CasaLegislativa, CasaLegislativa.objects.all()),
            'parlamentares': serializar(
                r, Parlamentar, Parlamentar.objects.filter(
                    id__in=parlamentares_ids)),
            'mandatos': serializar(r, Mandato, mandatos),
            'filiacoes': serializar(r, Filiacao, filiacoes),
            'partidos': serializar(r, Partido, Partido.objects.filter(
                id__in={f.partido_id for f in filiacoes})),
            'cargos_mesa': serializar(r, CargoMesa, CargoMesa.objects.all()),
            'integrantes_mesa': serializar(r, IntegranteMesa, mesa),
            'presencas_sessao': serializar(
                r, SessaoPlenariaPresenca, presencas),
            'presencas_ordem_dia': serializar(
                r, PresencaOrdemDia, presencas_ordem),
            'tipos_expediente': serializar(
                r, TipoExpediente, TipoExpediente.objects.all()),
            'expedientes': serializar(r, ExpedienteSessao, expedientes),
            'expedientes_materia': serializar(
                r, ExpedienteMateria, expedientes_materia),
            'ordens_dia': serializar(r, OrdemDia, ordens),
            'materias': serializar(r, MateriaLegislativa, materias),
            'autorias': serializar(r, Autoria, autorias),
            'autores': serializar(r, Autor, autores.values()),
            'tipos_autor': serializar(r, TipoAutor, TipoAutor.objects.all()),
            'tipos_resultado_votacao': serializar(
                r, TipoResultadoVotacao, TipoResultadoVotacao.objects.all()),
            'registros_votacao': serializar(
                r, RegistroVotacao, registros_votacao),
            'votos': serializar(r, VotoParlamentar, votos),
            'registros_leitura': serializar(
                r, RegistroLeitura, registros_leitura),
            'oradores': serializar(r, Orador, oradores[Orador]),
            'oradores_expediente': serializar(
                r, OradorExpediente, oradores[OradorExpediente]),
            'oradores_ordem_dia': serializar(
                r, OradorOrdemDia, oradores[OradorOrdemDia]),
        }
