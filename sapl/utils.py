from django.apps import apps
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

# SAPL business apps
#  This is a dependency order: each entry depends only on previous ones
#  The order is important for migration code
appconfs = [apps.get_app_config(n) for n in [
    'parlamentares',
    'comissoes',
    'compilacao',
    'materia',
    'norma',
    'sessao',
    'lexml',
    'protocoloadm', ]]


def register_all_models_in_admin(module_name):
    appname = module_name.split('.')[0]
    app = apps.get_app_config(appname)
    for model in app.get_models():
        class CustomModelAdmin(admin.ModelAdmin):
            list_display = [f.name for f in model._meta.fields
                            if f.name != 'id']

        if not admin.site.is_registered(model):
            admin.site.register(model, CustomModelAdmin)


def make_choices(*choice_pairs):
    assert len(choice_pairs) % 2 == 0
    ipairs = iter(choice_pairs)
    choices = list(zip(ipairs, ipairs))
    yield choices
    for key, value in choices:
        yield key

YES_NO_CHOICES = [(True, _('Sim')), (False, _('Não'))]


def int_to_roman(int_value):
    # if isinstance(int_value, type(1)):
    #    raise TypeError("expected integer, got %s" % type(int_value))
    if not 0 < int_value < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC',
            'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = ""
    for i in range(len(ints)):
        count = int(int_value / ints[i])
        result += nums[i] * count
        int_value -= ints[i] * count
    return result


def int_to_letter(int_value):
    result = ''
    int_value -= 1
    while int_value >= 26:
        rest = int_value % 26
        int_value = int(int_value / 26) - 1
        result = chr(rest + 65) + result
    result = chr(int_value + 65) + result
    return result
