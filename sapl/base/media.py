import mimetypes
import os
import re
from urllib.parse import quote

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse

from sapl.materia.models import Proposicao, pode_ver_proposicao
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo,
                                      pode_ver_documento_adm)
from sapl.sessao.models import (JustificativaAusencia, Orador,
                                OradorExpediente, OradorOrdemDia,
                                SessaoPlenaria, restringe_sessoes_visiveis)
from sapl.utils import EXTENSOES_ATIVAS, tipo_ativo

X_ACCEL_PREFIX = '/media-interna/'

# Arquivos que dependem de autorização, em private/ ou em qualquer outra
# pasta (public/ guarda os enviados antes da criação de private/).
PROTEGIDO_RE = re.compile(
    r'^sapl/[^/]+/(?:documentoadministrativo|'
    r'documentoacessorioadministrativo|proposicao)/')

RESOLVEDORES = {
    'documentoadministrativo': (
        DocumentoAdministrativo, 'texto_integral', pode_ver_documento_adm),
    'documentoacessorioadministrativo': (
        DocumentoAcessorioAdministrativo, 'arquivo',
        lambda user, obj: pode_ver_documento_adm(user, obj.documento)),
    'proposicao': (
        Proposicao, 'texto_original', pode_ver_proposicao),
}


# Arquivos gravados em sapl/public/<model>/<pk>/..., que seguem a
# visibilidade da sessão plenária a que pertencem.
MODELOS_DE_SESSAO = {m._meta.model_name: m for m in (
    SessaoPlenaria, Orador, OradorExpediente, OradorOrdemDia,
    JustificativaAusencia)}


def _de_sessao_oculta(request, partes):
    model = MODELOS_DE_SESSAO.get(partes[2])
    if request.user.is_authenticated or not model or len(partes) < 5 or \
            partes[1] != 'public' or not partes[3].isdigit():
        return False
    if model is SessaoPlenaria:
        sessoes = SessaoPlenaria.objects.filter(pk=partes[3])
    else:
        sessoes = SessaoPlenaria.objects.filter(
            pk__in=model.objects.filter(pk=partes[3]).values(
                'sessao_plenaria_id'))
    return sessoes.exists() and not restringe_sessoes_visiveis(
        sessoes, request.user).exists()


def _nome_protegido(request, path):
    """Devolve o nome do arquivo gravado no objeto dono, se o usuário puder
    vê-lo. O caminho servido vem do banco, nunca da URL."""
    resolvedor = RESOLVEDORES.get(path.split('/')[2])
    if not resolvedor:
        raise Http404
    model, campo, pode_ver = resolvedor
    obj = model.objects.filter(
        **{campo + '__in': [path, './' + path]}).first()
    if not obj:
        raise Http404
    arquivo = getattr(obj, campo)
    if not arquivo or not pode_ver(request.user, obj):
        raise Http404
    return arquivo.name[2:] if arquivo.name.startswith('./') else arquivo.name


def media(request, path):
    partes = path.split('/')
    if any(p in ('', '.', '..') for p in partes) or '\x00' in path:
        raise Http404

    protegido = path.startswith('sapl/private/') or bool(
        PROTEGIDO_RE.match(path))
    nome = _nome_protegido(request, path) if protegido else path

    if len(partes) > 2 and _de_sessao_oculta(request, partes):
        raise Http404
    nome_arquivo = os.path.basename(nome)

    content_type = (mimetypes.guess_type(nome_arquivo)[0] or
                    'application/octet-stream')
    disposicao = 'inline'
    if os.path.splitext(nome_arquivo)[1].lower() in EXTENSOES_ATIVAS or \
            tipo_ativo(content_type):
        content_type, disposicao = 'application/octet-stream', 'attachment'

    if settings.DEBUG:
        try:
            response = FileResponse(
                open(os.path.join(settings.MEDIA_ROOT, nome), 'rb'),
                content_type=content_type)
        except (FileNotFoundError, IsADirectoryError):
            raise Http404
    else:
        response = HttpResponse(content_type=content_type)
        response['X-Accel-Redirect'] = X_ACCEL_PREFIX + quote(nome)

    response['Content-Disposition'] = "%s; filename*=UTF-8''%s" % (
        disposicao, quote(nome_arquivo))
    response['X-Content-Type-Options'] = 'nosniff'
    if protegido:
        response['Cache-Control'] = 'private'
    return response
