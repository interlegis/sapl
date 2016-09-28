from compressor.utils import get_class
from django import template

from sapl.base.models import AppConfig
from sapl.parlamentares.models import Filiacao
from sapl.utils import permissoes_adm

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
def get_doc_adm_template_perms(user):
    app_config = AppConfig.objects.last()

    if app_config:
        if app_config.documentos_administrativos == 'O':
            return True

    return user.has_perms(permissoes_adm())


@register.filter
def ver_menu_sistema_perm(value):
    u = value
    if u.groups.filter(name='Operador Geral').exists() or u.is_superuser:
        return True
    else:
        return False


@register.filter
def ultima_filiacao(value):
    parlamentar = value

    ultima_filiacao = Filiacao.objects.filter(
        parlamentar=parlamentar).order_by('-data').first()

    if ultima_filiacao:
        return ultima_filiacao.partido
    else:
        return None
