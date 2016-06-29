from datetime import date
from functools import wraps
import os.path

from compressor.utils import get_class
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.checks import Warning, register
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from floppyforms import ClearableFileInput
import magic


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
        mime = mime.decode()
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


def permissoes_materia():
    lista_permissoes = []
    cts = ContentType.objects.filter(app_label='materia')
    perms_materia = list(Permission.objects.filter(content_type__in=cts))
    for p in perms_materia:
        lista_permissoes.append('materia.' + p.codename)
    return set(lista_permissoes)


def permissoes_comissoes():
    lista_permissoes = []
    cts = ContentType.objects.filter(app_label='comissoes')
    perms_comissoes = list(Permission.objects.filter(content_type__in=cts))
    for p in perms_comissoes:
        lista_permissoes.append('comissoes.' + p.codename)
    return set(lista_permissoes)


def permissoes_norma():
    lista_permissoes = []
    cts = ContentType.objects.filter(app_label='norma')
    perms_norma = list(Permission.objects.filter(content_type__in=cts))
    for p in perms_norma:
        lista_permissoes.append('norma.' + p.codename)
    return set(lista_permissoes)


def permissoes_parlamentares():
    lista_permissoes = []
    cts = ContentType.objects.filter(app_label='parlamentares')
    perms_parlamentares = list(Permission.objects.filter(content_type__in=cts))
    for p in perms_parlamentares:
        lista_permissoes.append('parlamentares.' + p.codename)
    return set(lista_permissoes)


def permissoes_protocoloadm():
    lista_permissoes = []
    perms_protocolo = Permission.objects.filter(
        group__name='Operador de Protocolo')
    for p in perms_protocolo:
        lista_permissoes.append('protocoloadm.' + p.codename)
    return set(lista_permissoes)


def permissoes_adm():
    lista_permissoes = []
    perms_adm = Permission.objects.filter(
        group__name='Operador de Administração')
    for p in perms_adm:
        lista_permissoes.append('protocoloadm.' + p.codename)
    return set(lista_permissoes)


def permissoes_sessao():
    lista_permissoes = []
    perms_sessao = list(Permission.objects.filter(
        group__name='Operador de Sessão'))
    for p in perms_sessao:
        lista_permissoes.append('sessao.' + p.codename)
    return set(lista_permissoes)


def permissoes_painel():
    lista_permissoes = []
    perms_painel = list(Permission.objects.filter(
        group__name='Operador de Painel'))
    for p in perms_painel:
        lista_permissoes.append('painel.' + p.codename)
    return set(lista_permissoes)


def permissao_tb_aux(self):
    if self.request.user.is_superuser:
        return True
    else:
        return False


def permissoes_autor():
    lista_permissoes = []
    perms_autor = list(Permission.objects.filter(
        group__name='Autor'))
    for p in perms_autor:
        lista_permissoes.append('materia.' + p.codename)
    return set(lista_permissoes)
