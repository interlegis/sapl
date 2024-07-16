from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls.conf import path, include
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
    path(r'^message$', TemplateView.as_view(template_name='base.html')),
    path(r'^admin/', admin.site.urls),

    path(r'', include(sapl.comissoes.urls)),
    path(r'', include(sapl.sessao.urls)),
    path(r'', include(sapl.parlamentares.urls)),
    path(r'', include(sapl.materia.urls)),
    path(r'', include(sapl.norma.urls)),
    path(r'', include(sapl.lexml.urls)),
    path(r'', include(sapl.painel.urls)),
    path(r'', include(sapl.protocoloadm.urls)),
    path(r'', include(sapl.compilacao.urls)),
    path(r'', include(sapl.relatorios.urls)),
    path(r'', include(sapl.audiencia.urls)),

    #    name='sapl_index'),
    # must come at the end
    #   so that base /sistema/ url doesn't capture its children
    path(r'', include(sapl.base.urls)),

    path(r'', include(sapl.api.urls)),

    path(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/sapl/img/favicon.ico', permanent=True)),

    path(r'', include(sapl.redireciona_urls.urls)),

    path("robots.txt", TemplateView.as_view(
        template_name="robots.txt", content_type="text/plain")),

    path(r'', include('django_prometheus.urls')),

]


# Fix a static asset finding error on Django 1.9 + gunicorn:
# http://stackoverflow.com/questions/35510373/

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path(r'^__debug__/', include(debug_toolbar.urls)),

    ]
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

    urlpatterns += [
        path(r'^media/(?P<path>.*)$', view_static_server, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
