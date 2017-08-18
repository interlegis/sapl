from compressor.utils import get_class
from django import template

from sapl.base.models import AppConfig
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.parlamentares import Filiacao
from sapl.utils import filiacao_data

register = template.Library()


@register.simple_tag
def field_verbose_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name


@register.simple_tag
def fieldclass_verbose_name(class_name, field_name):
    cls = get_class(class_name)
    return cls._meta.get_field(field_name).verbose_name


@register.simple_tag
def model_verbose_name(class_name):
    model = get_class(class_name)
    return model._meta.verbose_name


@register.simple_tag
def model_verbose_name_plural(class_name):
    model = get_class(class_name)
    return model._meta.verbose_name_plural


@register.filter
def lookup(d, key):
    return d[key] if key in d else []


@register.filter
def isinst(value, class_str):
    classe = value.__class__.__name__
    return classe == class_str


@register.filter
def get_add_perm(value, arg):
    perm = value
    view = arg

    try:
        nome_app = view.__class__.model._meta.app_label
    except AttributeError:
        return None
    nome_model = view.__class__.model.__name__.lower()
    can_add = '.add_' + nome_model

    return perm.__contains__(nome_app + can_add)


@register.filter
def get_change_perm(value, arg):
    perm = value
    view = arg

    try:
        nome_app = view.__class__.model._meta.app_label
    except AttributeError:
        return None
    nome_model = view.__class__.model.__name__.lower()
    can_change = '.change_' + nome_model

    return perm.__contains__(nome_app + can_change)


@register.filter
def get_delete_perm(value, arg):
    perm = value
    view = arg

    try:
        nome_app = view.__class__.model._meta.app_label
    except AttributeError:
        return None
    nome_model = view.__class__.model.__name__.lower()
    can_delete = '.delete_' + nome_model

    return perm.__contains__(nome_app + can_delete)


@register.filter
def ultima_filiacao(value):
    parlamentar = value

    ultima_filiacao = Filiacao.objects.filter(
        parlamentar=parlamentar).order_by('-data').first()

    if ultima_filiacao:
        return ultima_filiacao.partido
    else:
        return None


@register.filter
def get_config_attr(attribute):
    return AppConfig.attr(attribute)


@register.filter
def str2intabs(value):
    if not isinstance(value, str):
        return ''
    try:
        v = int(value)
        v = abs(v)
        return v
    except:
        return ''


@register.filter
def has_iframe(request):

    iframe = request.session.get('iframe', False)
    if not iframe and 'iframe' in request.GET:
        ival = request.GET['iframe']
        if ival and int(ival) == 1:
            request.session['iframe'] = True
            return True
    elif 'iframe' in request.GET:
        ival = request.GET['iframe']
        if ival and int(ival) == 0:
            del request.session['iframe']
            return False

    return iframe


@register.filter
def url(value):
    if value.startswith('http://') or value.startswith('https://'):
        return True
    return False


@register.filter
def cronometro_to_seconds(value):
    if not AppConfig.attr('cronometro_' + value):
        return 0

    m, s, x = AppConfig.attr(
        'cronometro_' + value).isoformat().split(':')

    return 60 * int(m) + int(s)


@register.filter
def to_list_pk(object_list):
    return [o.pk for o in object_list]


@register.filter
def search_get_model(object):
    if type(object) == MateriaLegislativa:
        return 'm'
    elif type(object) == DocumentoAcessorio:
        return 'd'
    elif type(object) == NormaJuridica:
        return 'n'

    return None


@register.filter
def urldetail_content_type(obj, value):
    return '%s:%s_detail' % (
        value._meta.app_config.name, obj.content_type.model)


@register.filter
def urldetail(obj):
    return '%s:%s_detail' % (
        obj._meta.app_config.name, obj._meta.model_name)


@register.filter
def filiacao_data_filter(parlamentar, data_inicio):
    return filiacao_data(parlamentar, data_inicio)


@register.filter
def filiacao_intervalo_filter(parlamentar, date_range):
    return filiacao_data(parlamentar, date_range[0], date_range[1])
