from django.conf.urls import patterns, url

from sapl.urls import urlpatterns as original_patterns


urlpatterns = original_patterns + patterns('',
    url(r'^zzzz$', 'home.views.index', name='zzzz'),
)
