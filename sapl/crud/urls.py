from django.urls.conf import re_path, include

urlpatterns = [
    re_path(r'', include('stub_app.urls')),
]
