from django.apps import apps
from django.contrib import admin


appname = __name__.split('.')[0]
app = apps.get_app_config(appname)

for model in app.get_models():
    admin.site.register(model)
