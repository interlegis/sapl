import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.dateparse import parse_datetime as django_parse_datetime
from django.utils.safestring import mark_safe
from webpack_loader import utils

from sapl.base.models import AppConfig
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa, Proposicao
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Filiacao
from sapl.sessao.models import SessaoPlenaria
from sapl.utils import filiacao_data, SEPARADOR_HASH_PROPOSICAO, is_report_allowed

register = template.Library()


def get_class(class_string):
    if not hasattr(class_string, '__bases__'):
        class_string = str(class_string)
        dot = class_string.rindex('.')
        mod_name, class_name = class_string[:dot], class_string[dot + 1:]
        if class_name:
            return getattr(__import__(mod_name, {}, {}, [str('')]), class_name)


@register.simple_tag
def define(arg):
    return arg


@register.simple_tag
def describe_operation(value):
    if value == "C":
        return "Criar"
    elif value == "D":
        return "Apagar"
    elif value == "U":
        return "Atualizar"
    return ""


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
def obfuscate_value(value, key):
    if key in ["hash", "google_recaptcha_secret_key", "password", "google_recaptcha_site_key", "hash_code"]:
        return "***************"
    return value


@register.filter
def desc_operation(value):
    if value == "C":
        return "Criado"
    elif value == "D":
        return "Excluido"
    elif value == "U":
        return "Atualizado"
    return ""


@register.filter
def format_user(user):
    if user.first_name:
        return user.first_name + " " + user.last_name + " (" + user.username + ")"
    else:
        return user.username


@register.filter
def meta_model_value(instance, attr):
    try:
        return getattr(instance._meta, attr)
    except:
        return ''


@register.filter
def split(value, arg):
    return value.split(arg)


@register.filter
def to_str(arg):
    return str(arg)


@register.filter
def get_last_item_from_list(list, arg):
    return list[arg]


@register.filter
def sort_by_keys(value, key):
    transformed = []
    id_props = [x.id for x in value]
    qs = Proposicao.objects.filter(pk__in=id_props)
    key_descricao = {'1': 'data_envio',
                     '-1': '-data_envio',
                     '2': 'tipo',
                     '-2': '-tipo',
                     '3': 'descricao',
                     '-3': '-descricao',
                     '4': 'autor',
                     '-4': '-autor'
                     }

    transformed = qs.order_by(key_descricao[key])
    return transformed


@register.filter
def paginacao_limite_inferior(pagina):
    return (int(pagina) - 1) * 10


@register.filter
def paginacao_limite_superior(pagina):
    return int(pagina) * 10


@register.filter
def resultado_votacao(materia):
    ra = materia.registrovotacao_set.last()
    rb = materia.retiradapauta_set.last()
    rl = materia.registroleitura_set.last()

    if ra:
        resultado = ra.tipo_resultado_votacao.nome
    elif rb:
        resultado = rb.tipo_de_retirada.descricao
    elif rl:
        resultado = "Matéria lida"
    else:
        resultado = ""
    return resultado


@register.filter
def lookup(d, key):
    return d[key] if key in d else []


@register.filter
def isinst(value, class_str):
    classe = value.__class__.__name__
    return classe == class_str


@register.filter
@stringfilter
def strip_hash(value):
    vet = value.split('/')
    if len(vet) == 2:
        return vet[0][1:]
    else:
        return value.split(SEPARADOR_HASH_PROPOSICAO)[0][1:]


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
def audio_url(value):
    return True if url(value) and value.endswith("mp3") else False


@register.filter
def is_video_url(value):
    video_extensions = ["mp4", "ogg", "webm", "3gp", "ogv"]
    has_ext = any([value.endswith(i) for i in video_extensions])
    return url(value) and has_ext


@register.filter
def youtube_url(value):
    # Test if YouTube video
    # tested on https://pythex.org/
    value = value.lower()
    youtube_pattern = "^((https?://)?(www\.)?youtube\.com\/watch\?v=)"
    r = re.findall(youtube_pattern, value)
    return True if r else False


@register.filter
def facebook_url(value):
    value = value.lower()
    facebook_pattern = "^((https?://)?((www|pt-br)\.)?facebook\.com(\/.+)?\/videos(\/.*)?)"
    r = re.findall(facebook_pattern, value)
    return True if r else False


@register.filter
def youtube_id(value):
    from urllib.parse import urlparse, parse_qs
    u_pars = urlparse(value)
    quer_v = parse_qs(u_pars.query).get('v')
    if quer_v:
        return quer_v[0]
    return ''


@register.filter
def file_extension(value):
    import pathlib
    return pathlib.Path(value).suffix.replace('.', '')


@register.filter
def cronometro_to_seconds(value):
    if not AppConfig.attr('cronometro_' + value):
        return 0

    return AppConfig.attr('cronometro_' + value).seconds


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
    elif type(object) == SessaoPlenaria:
        return 's'

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
    try:
        filiacao = filiacao_data(parlamentar, data_inicio)
    except Exception:
        filiacao = ''
    return filiacao


@register.filter
def filiacao_intervalo_filter(parlamentar, date_range):
    try:
        filiacao = filiacao_data(parlamentar, date_range[0], date_range[1])
    except Exception:
        filiacao = ''
    return filiacao


@register.simple_tag
def render_chunk_vendors(extension=None):
    try:
        tags = utils.get_as_tags(
            'chunk-vendors', extension=extension, config='DEFAULT', attrs='')
        return mark_safe('\n'.join(tags))
    except:
        return ''


@register.filter(is_safe=True)
@stringfilter
def dont_break_out(value):
    _safe = '<div class="dont-break-out">{}</div>'.format(value)
    _safe = mark_safe(_safe)
    return _safe


@register.filter(expects_localtime=True)
def parse_datetime(value):
    return django_parse_datetime(value)


@register.filter
def is_report_visible(request, url_path=None):
    return is_report_allowed(request, url_path)


@register.filter
def sort_by_index(queryset, index):
    return sorted(queryset, key=lambda x: x[index])