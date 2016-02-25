from functools import wraps

from django.apps import apps
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


def register_all_models_in_admin(module_name):
    appname = module_name.split('.')[0]
    app = apps.get_app_config(appname)
    for model in app.get_models():
        class CustomModelAdmin(admin.ModelAdmin):
            list_display = [f.name for f in model._meta.fields
                            if f.name != 'id']

        if not admin.site.is_registered(model):
            admin.site.register(model, CustomModelAdmin)


def xstr(s):
    return '' if s is None else str(s)


def create_barcode(value):
    '''
        creates a base64 encoded barcode PNG image
    '''
    from base64 import b64encode
    from reportlab.graphics.barcode import createBarcodeDrawing

    barcode = createBarcodeDrawing('Code128',
                                   value=value,
                                   barWidth=170,
                                   height=50,
                                   fontSize=2,
                                   humanReadable=True)
    data = b64encode(barcode.asString('png'))
    return data.decode('utf-8')


YES_NO_CHOICES = [(True, _('Sim')), (False, _('Não'))]


def listify(function):
    @wraps(function)
    def f(*args, **kwargs):
        return list(function(*args, **kwargs))
    return f
