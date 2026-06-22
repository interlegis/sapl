"""
serve_media — X-Accel-Redirect gate for all /media/ files.

Production flow (nginx proxies /media/ to Gunicorn):
  1. Django middleware runs (IP rate-limit, bot UA check, etc.).
  2. serve_media() runs auth check for sapl/private/, writes
     URL-path counter to Redis DB 1, then returns X-Accel-Redirect.
     Nginx serves the bytes directly from disk — Gunicorn worker freed immediately.

Development flow (DEBUG=True, nginx absent):
  Falls back to django.views.static.serve for live file serving.

Redis side-effects per request (DB 1, TTL=MEDIA_PATH_COUNTER_TTL):
  rl:{ns}:path:{sha256('/media/<path>')}:reqs  — URL-path access counter
"""

import hashlib
import mimetypes
import os
from urllib.parse import quote

from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.static import serve

from sapl import settings as sapl_settings
from sapl.middleware.ratelimit import (
    _NAMESPACE,
    RL_PATH_REQUESTS,
    _incr_with_ttl,
)


def _safe_resolve(rel_path):
    """
    Return the absolute path of rel_path inside MEDIA_ROOT.
    Raises Http404 if the resolved path would escape the root
    (path traversal guard).
    """
    abs_root = os.path.abspath(settings.MEDIA_ROOT)
    abs_path = os.path.abspath(os.path.join(abs_root, rel_path))
    if not abs_path.startswith(abs_root + os.sep) and abs_path != abs_root:
        raise Http404
    return abs_path


def _is_public_docadm(path):
    # Documentos Administrativos são sempre salvos na pasta /private,
    # mas podem ter acesso público liberado como OSTENSIVO ou requerer
    # autenticacao se for DOC_ADM_RESTRITIVO
    from sapl.base.models import AppConfig, DOC_ADM_OSTENSIVO
    return 'documentoadministrativo' in path and \
           AppConfig.attr('documentos_administrativos') == DOC_ADM_OSTENSIVO


def serve_media(request, path):
    """
    Registered in sapl/urls.py for both DEBUG and production.
    Route: ^media/(?P<path>.*)$
    """
    # Path traversal guard — raises Http404 on escape attempt.
    abs_path = _safe_resolve(path)

    # Auth gate for private documents — redirect to login if anonymous.
    if path.startswith('sapl/private/') and not _is_public_docadm(path):
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())

    # 404 before writing any counters.
    if not os.path.isfile(abs_path):
        raise Http404

    # URL-path counter (DB 1).
    _incr_with_ttl(
        RL_PATH_REQUESTS.format(ns=_NAMESPACE, sha256=hashlib.sha256(f'/media/{path}'.encode()).hexdigest()),
        ttl=sapl_settings.MEDIA_PATH_COUNTER_TTL,
    )

    if settings.DEBUG:
        # Development: no nginx present; serve the file directly.
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    # Production: tell nginx to serve the file from the internal location.
    filename = os.path.basename(path)
    content_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(content_type=content_type or 'application/octet-stream')
    response['X-Accel-Redirect'] = f'/internal/media/{path}'
    response['Content-Disposition'] = f"inline; filename*=UTF-8''{quote(filename)}"
    response['Cache-Control'] = 'public, max-age=86400, stale-while-revalidate=3600'
    response['X-Robots-Tag'] = 'noindex'
    return response
