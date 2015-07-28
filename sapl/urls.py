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
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'', include('comissoes.urls')),
    url(r'', include('sessao.urls')),
    url(r'', include('parlamentares.urls')),
    url(r'', include('materia.urls')),
    url(r'', include('norma.urls')),
    url(r'', include('lexml.urls')),

    # must come at the end
    #   so that base /sistema/ url doesn't capture its children
    url(r'', include('base.urls')),
]
