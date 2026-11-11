from django.apps.registry import apps
from django.db.models import Q

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.compilacao.models import (STATUS_TA_EDITION,
                                    STATUS_TA_IMMUTABLE_PUBLIC,
                                    STATUS_TA_IMMUTABLE_RESTRICT,
                                    STATUS_TA_PUBLIC, Dispositivo,
                                    TextoArticulado)


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('compilacao')
    ]
)


def textos_articulados_visiveis(user):
    """
    Textos Articulados que o usuário pode ver, com as mesmas regras de
    TextoArticulado.has_view_permission, usada pelas telas de compilação:

    - público (0) e imutável público (69): todos;
    - donos do texto: sempre, qualquer que seja a privacidade;
    - imutável restrito (79): quem tem view_restricted_textoarticulado;
    - em edição (89): quem tem change_dispositivo_edicao_dinamica;
    - privado (99): apenas os donos.
    """
    q = Q(privacidade__in=(STATUS_TA_PUBLIC, STATUS_TA_IMMUTABLE_PUBLIC))

    if user.is_authenticated:
        q |= Q(pk__in=TextoArticulado.objects.filter(
            owners=user).values('pk'))

        if user.has_perm('compilacao.view_restricted_textoarticulado'):
            q |= Q(privacidade=STATUS_TA_IMMUTABLE_RESTRICT)

        if user.has_perm('compilacao.change_dispositivo_edicao_dinamica'):
            q |= Q(privacidade=STATUS_TA_EDITION)

    return TextoArticulado.objects.filter(q)


@customize(TextoArticulado)
class _TextoArticuladoViewSet:

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(pk__in=textos_articulados_visiveis(
            self.request.user).values('pk'))


@customize(Dispositivo)
class _DispositivoViewSet:

    def get_queryset(self):
        """
        Como na tela do texto (TextView), um dispositivo aparece no texto a
        que pertence (ta) e, quando tem visibilidade, também no bloco de
        alteração do texto que o publicou (ta_publicado), conforme
        compilacao/text_list_blocoalteracao.html.
        """
        qs = super().get_queryset()
        tas = textos_articulados_visiveis(self.request.user).values('pk')
        return qs.filter(
            Q(ta__in=tas) | Q(ta_publicado__in=tas, visibilidade=True))
