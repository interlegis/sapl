from datetime import date
from functools import wraps
from unicodedata import normalize as unicodedata_normalize
import hashlib

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import ugettext_lazy as _
from floppyforms import ClearableFileInput
import magic


def normalize(txt):
    return unicodedata_normalize(
        'NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def get_settings_auth_user_model():
    return getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


autor_label = '''
    <div class="col-xs-12">
       Autor: <span id="nome_autor" name="nome_autor">
                {% if form.autor.value %}
                    {{form.autor.value}}
                {% endif %}
              </span>
    </div>
'''


autor_modal = '''
   <div id="modal_autor" title="Selecione o Autor" align="center">
       <form>
           <input id="q" type="text" />
           <input id="pesquisar" type="submit" value="Pesquisar"
               class="btn btn-primary btn-sm"/>
       </form>
       <div id="div-resultado"></div>
       <input type="submit" id="selecionar" value="Selecionar"
              hidden="true" />
   </div>
'''


class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'floppyforms/image_thumbnail.html'


class RangeWidgetOverride(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Inicial'}),
                   forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Final'}))
        super(RangeWidgetOverride, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        html = '<div class="col-sm-6">%s</div><div class="col-sm-6">%s</div>'\
            % tuple(rendered_widgets)
        return '<div class="row">%s</div>' % html


def register_all_models_in_admin(module_name):
    appname = module_name.split('.')
    appname = appname[1] if appname[0] == 'sapl' else appname[0]
    app = apps.get_app_config(appname)
    for model in app.get_models():
        class CustomModelAdmin(admin.ModelAdmin):
            list_display = [f.name for f in model._meta.fields
                            if f.name != 'id']

        if not admin.site.is_registered(model):
            admin.site.register(model, CustomModelAdmin)


def xstr(s):
    return '' if s is None else str(s)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_base_url(request):
    # TODO substituir por Site.objects.get_current().domain
    # from django.contrib.sites.models import Site

    current_domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    return "{0}://{1}".format(protocol, current_domain)


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

TURNO_TRAMITACAO_CHOICES = [
    ('P', _('Primeiro')),
    ('S', _('Segundo')),
    ('U', _('Único')),
    ('L', _('Suplementar')),
    ('F', _('Final')),
    ('A', _('Votação única em Regime de Urgência')),
    ('B', _('1ª Votação')),
    ('C', _('2ª e 3ª Votação')),
]

INDICADOR_AFASTAMENTO = [
    ('A', _('Afastamento')),
    ('F', _('Fim de Mandato')),
]


def listify(function):
    @wraps(function)
    def f(*args, **kwargs):
        return list(function(*args, **kwargs))
    return f

UF = [
    ('AC', 'Acre'),
    ('AL', 'Alagoas'),
    ('AP', 'Amapá'),
    ('AM', 'Amazonas'),
    ('BA', 'Bahia'),
    ('CE', 'Ceará'),
    ('DF', 'Distrito Federal'),
    ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'),
    ('MA', 'Maranhão'),
    ('MT', 'Mato Grosso'),
    ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'),
    ('PR', 'Paraná'),
    ('PB', 'Paraíba'),
    ('PA', 'Pará'),
    ('PE', 'Pernambuco'),
    ('PI', 'Piauí'),
    ('RJ', 'Rio de Janeiro'),
    ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'),
    ('RO', 'Rondônia'),
    ('RR', 'Roraima'),
    ('SC', 'Santa Catarina'),
    ('SE', 'Sergipe'),
    ('SP', 'São Paulo'),
    ('TO', 'Tocantins'),
    ('EX', 'Exterior'),
]

RANGE_ANOS = [(year, year) for year in range(date.today().year, 1889, -1)]

RANGE_MESES = [
    (1, 'Janeiro'),
    (2, 'Fevereiro'),
    (3, 'Março'),
    (4, 'Abril'),
    (5, 'Maio'),
    (6, 'Junho'),
    (7, 'Julho'),
    (8, 'Agosto'),
    (9, 'Setembro'),
    (10, 'Outubro'),
    (11, 'Novembro'),
    (12, 'Dezembro'),
]

RANGE_DIAS_MES = [(n, n) for n in range(1, 32)]

TIPOS_TEXTO_PERMITIDOS = (
    'application/vnd.oasis.opendocument.text',
    'application/x-vnd.oasis.opendocument.text',
    'application/pdf',
    'application/x-pdf',
    'application/acrobat',
    'applications/vnd.pdf',
    'text/pdf',
    'text/x-pdf',
    'text/plain',
    'application/txt',
    'browser/internal',
    'text/anytext',
    'widetext/plain',
    'widetext/paragraph',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/xml',
    'text/xml',
    'text/html',
)

TIPOS_IMG_PERMITIDOS = (
    'image/jpeg',
    'image/jpg',
    'image/jpe_',
    'image/pjpeg',
    'image/vnd.swiftview-jpeg',
    'application/jpg',
    'application/x-jpg',
    'image/pjpeg',
    'image/pipeg',
    'image/vnd.swiftview-jpeg',
    'image/x-xbitmap',
    'image/bmp',
    'image/x-bmp',
    'image/x-bitmap',
    'image/png',
    'application/png',
    'application/x-png',
)


def fabrica_validador_de_tipos_de_arquivo(lista, nome):

    def restringe_tipos_de_arquivo(value):
        mime = magic.from_buffer(value.read(), mime=True)
        if mime not in lista:
            raise ValidationError(_('Tipo de arquivo não suportado'))
    # o nome é importante para as migrations
    restringe_tipos_de_arquivo.__name__ = nome
    return restringe_tipos_de_arquivo

restringe_tipos_de_arquivo_txt = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_TEXTO_PERMITIDOS, 'restringe_tipos_de_arquivo_txt')
restringe_tipos_de_arquivo_img = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_IMG_PERMITIDOS, 'restringe_tipos_de_arquivo_img')


def intervalos_tem_intersecao(a_inicio, a_fim, b_inicio, b_fim):
    maior_inicio = max(a_inicio, b_inicio)
    menor_fim = min(a_fim, b_fim)
    return maior_inicio <= menor_fim


def permissoes(nome_grupo, app_label):
    lista_permissoes = []
    try:
        perms = list(Permission.objects.filter(
            group__name=nome_grupo))
        for p in perms:
            lista_permissoes.append('%s.%s' % (app_label, p.codename))
    except:
        pass
    return set(lista_permissoes)


def permission_required_for_app(app_label, login_url=None,
                                raise_exception=False):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """
    def check_perms(user):
        if user.has_module_perms(app_label):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False
    return user_passes_test(check_perms, login_url=login_url)


def permissoes_materia():
    return permissoes('Operador de Matéria', 'materia')


def permissoes_comissoes():
    return permissoes('Operador de Comissões', 'comissoes')


def permissoes_norma():
    return permissoes('Operador de Norma Jurídica', 'norma')


def permissoes_protocoloadm():
    return permissoes('Operador de Protocolo Administrativo', 'protocoloadm')


def permissoes_adm():
    return permissoes('Operador Administrativo', 'protocoloadm')


def permissoes_sessao():
    return permissoes('Operador de Sessão Plenária', 'sessao')


def permissoes_painel():
    return permissoes('Operador de Painel Eletrônico', 'painel')


def permissoes_autor():
    return permissoes('Autor', 'materia')


def permissoes_parlamentares():
    lista_permissoes = []
    try:
        cts = ContentType.objects.filter(app_label='parlamentares')
        perms_parlamentares = list(Permission.objects.filter(
            content_type__in=cts))
        for p in perms_parlamentares:
            lista_permissoes.append('parlamentares.' + p.codename)
    except:
        pass
    return set(lista_permissoes)


def permissao_tb_aux(self):
    u = self.request.user
    if u.groups.filter(name='Operador Geral').exists() or u.is_superuser:
        return True
    else:
        return False


def gerar_hash_arquivo(arquivo, pk, block_size=2**20):
    md5 = hashlib.md5()
    arq = open(arquivo, 'rb')
    while True:
        data = arq.read(block_size)
        if not data:
            break
        md5.update(data)
    return 'P' + md5.hexdigest() + '/' + pk
