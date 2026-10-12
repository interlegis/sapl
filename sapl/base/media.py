import mimetypes
import os
import re
from urllib.parse import quote

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse

from sapl.materia.models import Proposicao
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo,
                                      pode_ver_documento_adm)
from sapl.utils import EXTENSOES_ATIVAS

X_ACCEL_PREFIX = '/media-interna/'

# Arquivos que dependem de autorização. Inclui as pastas public/ onde
# ficaram os arquivos enviados antes da criação de private/.
PROTEGIDO_RE = re.compile(
    r'^sapl/(?:private|public/(?:documentoadministrativo|'
    r'documentoacessorioadministrativo|proposicao))/')


def _pode_ver_proposicao(user, proposicao):
    if proposicao.data_recebimento:
        return True
    if not user.is_authenticated:
        return False
    if proposicao.autor and proposicao.autor.operadores.filter(
            id=user.id).exists():
        return True
    return bool(proposicao.data_envio) and user.has_module_perms(
        'protocoloadm')


RESOLVEDORES = {
    'documentoadministrativo': (
        DocumentoAdministrativo, 'texto_integral', pode_ver_documento_adm),
    'documentoacessorioadministrativo': (
        DocumentoAcessorioAdministrativo, 'arquivo',
        lambda user, obj: pode_ver_documento_adm(user, obj.documento)),
    'proposicao': (
        Proposicao, 'texto_original', _pode_ver_proposicao),
}


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

    protegido = bool(PROTEGIDO_RE.match(path))
    nome = _nome_protegido(request, path) if protegido else path
    nome_arquivo = os.path.basename(nome)

    if os.path.splitext(nome_arquivo)[1].lower() in EXTENSOES_ATIVAS:
        content_type, disposicao = 'application/octet-stream', 'attachment'
    else:
        content_type = (mimetypes.guess_type(nome_arquivo)[0] or
                        'application/octet-stream')
        disposicao = 'inline'

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
