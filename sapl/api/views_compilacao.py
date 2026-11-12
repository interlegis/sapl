from django.apps.registry import apps
from django.db.models import Q

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.compilacao.models import (STATUS_TA_EDITION,
                                    STATUS_TA_IMMUTABLE_PUBLIC,
                                    STATUS_TA_IMMUTABLE_RESTRICT,
                                    STATUS_TA_PUBLIC, Dispositivo, Nota,
                                    Publicacao, TextoArticulado, Vide)


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


def q_dispositivos_visiveis(user, prefixo=''):
    """
    Filtro dos dispositivos que o usuário pode ver. Como na tela do texto
    (TextView), um dispositivo aparece no texto a que pertence (ta) e,
    quando tem visibilidade, também no bloco de alteração do texto que o
    publicou (ta_publicado), conforme
    compilacao/text_list_blocoalteracao.html.

    `prefixo` aplica a regra ao dispositivo de outro model, como em
    q_dispositivos_visiveis(user, 'dispositivo__') para Nota.
    """
    tas = textos_articulados_visiveis(user).values('pk')
    return Q(**{f'{prefixo}ta__in': tas}) | Q(**{
        f'{prefixo}ta_publicado__in': tas, f'{prefixo}visibilidade': True})


@customize(Dispositivo)
class _DispositivoViewSet:

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(q_dispositivos_visiveis(self.request.user))


@customize(Nota)
class _NotaViewSet:

    def get_queryset(self):
        """
        Como na tela do texto (compilacao/text_list_bloco.html), uma nota
        aparece com o dispositivo a que pertence e conforme a publicidade:

        - superusuário: todas;
        - pública: todos;
        - institucional: usuários autenticados;
        - privada: só o dono da nota (owner).
        """
        qs = super().get_queryset()
        user = self.request.user
        qs = qs.filter(q_dispositivos_visiveis(user, 'dispositivo__'))
        if user.is_superuser:
            return qs

        q = Q(publicidade=Nota.NPUBL)
        if user.is_authenticated:
            q |= Q(publicidade=Nota.NINST)
            q |= Q(publicidade=Nota.NPRIV, owner=user)
        return qs.filter(q)


@customize(Vide)
class _VideViewSet:

    def get_queryset(self):
        """
        Na tela do texto (TextView), um vide aparece no texto do
        dispositivo_base (cita) e no do dispositivo_ref (citado). Basta que
        um dos dois dispositivos seja visível.
        """
        qs = super().get_queryset()
        user = self.request.user
        return qs.filter(
            q_dispositivos_visiveis(user, 'dispositivo_base__') |
            q_dispositivos_visiveis(user, 'dispositivo_ref__'))


@customize(Publicacao)
class _PublicacaoViewSet:

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(ta__in=textos_articulados_visiveis(
            self.request.user).values('pk'))
