from django.urls.conf import path, include

urlpatterns = [
    path(r'', include('stub_app.urls')),
]
