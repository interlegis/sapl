"""sapl URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView, TemplateView
from django.views.static import serve as view_static_server

import sapl.api.urls
import sapl.audiencia.urls
import sapl.base.urls
import sapl.comissoes.urls
import sapl.compilacao.urls
import sapl.lexml.urls
import sapl.materia.urls
import sapl.norma.urls
import sapl.painel.urls
import sapl.parlamentares.urls
import sapl.protocoloadm.urls
import sapl.redireciona_urls.urls
import sapl.relatorios.urls
import sapl.sessao.urls

from sapl.api.views_health import AppzVersionView, HealthzView, ReadyzView

urlpatterns = []

urlpatterns += [
    url(r'^message$', TemplateView.as_view(template_name='base.html')),
    url(r'^admin/', admin.site.urls),

    url(r'', include(sapl.comissoes.urls)),
    url(r'', include(sapl.sessao.urls)),
    url(r'', include(sapl.parlamentares.urls)),
    url(r'', include(sapl.materia.urls)),
    url(r'', include(sapl.norma.urls)),
    url(r'', include(sapl.lexml.urls)),
    url(r'', include(sapl.painel.urls)),
    url(r'', include(sapl.protocoloadm.urls)),
    url(r'', include(sapl.compilacao.urls)),
    url(r'', include(sapl.relatorios.urls)),
    url(r'', include(sapl.audiencia.urls)),

    #    name='sapl_index'),
    # must come at the end
    #   so that base /sistema/ url doesn't capture its children
    url(r'', include(sapl.base.urls)),

    url(r'', include(sapl.api.urls)),

    url(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/sapl/img/favicon.ico', permanent=True)),

    url(r'', include(sapl.redireciona_urls.urls)),

    path("robots.txt", TemplateView.as_view(
        template_name="robots.txt", content_type="text/plain")),

    # Health and Readiness
    url(r'^version/$', AppzVersionView.as_view(), name="version"),
    url(r"^health/$", HealthzView.as_view(), name="health"),
    url(r"^ready/$", ReadyzView.as_view(), name="ready"),

    # Monitoring
    path(r'', include('django_prometheus.urls')),

]


# Media files — served via X-Accel-Redirect in production, directly in DEBUG.
from sapl.base.media import serve_media  # noqa: E402

urlpatterns += [
    url(r'^media/(?P<path>.*)$', serve_media, name='serve_media'),
]

# Fix a static asset finding error on Django 1.9 + gunicorn:
# http://stackoverflow.com/questions/35510373/

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),

    ]
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

    # media/ is handled by serve_media below (works in DEBUG too)


# Make the rate limiter return 429 (Too Many Requests) instead of 403 (Forbidden Access)
def custom_permission_denied_view(request, exception=None):
    from django.http import HttpResponse, HttpResponseForbidden
    from ratelimit.exceptions import Ratelimited

    if isinstance(exception, Ratelimited):
        resp = HttpResponse('Too many requests', status=429)
        resp['Retry-After'] = '60'
        return resp
    return HttpResponseForbidden('Forbidden')


handler403 = custom_permission_denied_view
