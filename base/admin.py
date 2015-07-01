from django.apps import apps
from django.contrib import admin

appname = __name__.split('.')[0]
app = apps.get_app_config(appname)
for model in app.get_models():
    class CustomModelAdmin(admin.ModelAdmin):
        list_display = [f.name for f in model._meta.fields if f.name != 'id']

    if not admin.site.is_registered(model):
        admin.site.register(model, CustomModelAdmin)
