from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls.conf import re_path, include
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


urlpatterns = []

urlpatterns += [
    re_path(r'^message$', TemplateView.as_view(template_name='base.html')),
    re_path(r'^admin/', admin.site.urls),

    re_path(r'', include(sapl.comissoes.urls)),
    re_path(r'', include(sapl.sessao.urls)),
    re_path(r'', include(sapl.parlamentares.urls)),
    re_path(r'', include(sapl.materia.urls)),
    re_path(r'', include(sapl.norma.urls)),
    re_path(r'', include(sapl.lexml.urls)),
    re_path(r'', include(sapl.painel.urls)),
    re_path(r'', include(sapl.protocoloadm.urls)),
    re_path(r'', include(sapl.compilacao.urls)),
    re_path(r'', include(sapl.relatorios.urls)),
    re_path(r'', include(sapl.audiencia.urls)),

    #    name='sapl_index'),
    # must come at the end
    #   so that base /sistema/ url doesn't capture its children
    re_path(r'', include(sapl.base.urls)),

    re_path(r'', include(sapl.api.urls)),

    re_path(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/sapl/img/favicon.ico', permanent=True)),

    re_path(r'', include(sapl.redireciona_urls.urls)),

    re_path("robots.txt", TemplateView.as_view(
        template_name="robots.txt", content_type="text/plain")),

    re_path(r'', include('django_prometheus.urls')),

]


# Fix a static asset finding error on Django 1.9 + gunicorn:
# http://stackoverflow.com/questions/35510373/

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),

    ]
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', view_static_server, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
