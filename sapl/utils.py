from datetime import date
from functools import wraps
from unicodedata import normalize as unicodedata_normalize
import hashlib
import logging
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button
from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.fields import (GenericForeignKey, GenericRel,
                                                GenericRelation)
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from floppyforms import ClearableFileInput
import django_filters
import magic

from sapl.crispy_layout_mixin import SaplFormLayout, form_actions, to_row
from sapl.settings import BASE_DIR


sapl_logger = logging.getLogger(BASE_DIR.name)


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


def montar_row_autor(name):
    autor_row = to_row(
        [(name, 0),
         (Button('pesquisar',
                 'Pesquisar Autor',
                 css_class='btn btn-primary btn-sm'), 2),
         (Button('limpar',
                 'Limpar Autor',
                 css_class='btn btn-primary btn-sm'), 10)])

    return autor_row


def montar_helper_autor(self):
    autor_row = montar_row_autor('nome')
    self.helper = FormHelper()
    self.helper.layout = SaplFormLayout(*self.get_layout())

    # Adiciona o novo campo 'autor' e mecanismo de busca
    self.helper.layout[0][0].append(HTML(autor_label))
    self.helper.layout[0][0].append(HTML(autor_modal))
    self.helper.layout[0][1] = autor_row

    # Adiciona espaço entre o novo campo e os botões
    # self.helper.layout[0][4][1].append(HTML('<br /><br />'))

    # Remove botões que estão fora do form
    self.helper.layout[1].pop()

    # Adiciona novos botões dentro do form
    self.helper.layout[0][4][0].insert(2, form_actions(more=[
        HTML('<a href="{{ view.cancel_url }}"'
             ' class="btn btn-inverse">Cancelar</a>')]))


class SaplGenericForeignKey(GenericForeignKey):

    def __init__(
            self,
            ct_field='content_type',
            fk_field='object_id',
            for_concrete_model=True,
            verbose_name=''):
        super().__init__(ct_field, fk_field, for_concrete_model)
        self.verbose_name = verbose_name


class SaplGenericRelation(GenericRelation):
    """
    Extenção da class GenericRelation para implmentar o atributo fields_search

    fields_search é uma tupla de tuplas de dois strings no padrão de construção
        de campos porém com [Field Lookups][ref_1]

        exemplo:
            [No Model Parlamentar em][ref_2] existe a implementação dessa
            classe no atributo autor. Parlamentar possui três informações
            relevantes para buscas realacionadas a Autor:

                - nome_completo;
                - nome_parlamentar; e
                - filiacao__partido__sigla

            que devem ser pesquisados, coincidentemente
            pelo FieldLookup __icontains

            portanto a estrutura de fields_search seria:
                fields_search=(
                    ('nome_completo', '__icontains'),
                    ('nome_parlamentar', '__icontains'),
                    ('filiacao__partido__sigla', '__icontains'),
                )


    [ref_1]: https://docs.djangoproject.com/el/1.10/topics/db/queries/
             #field-lookups
    [ref_2]: https://github.com/interlegis/sapl/blob/master/sapl/
             parlamentares/models.py
    """

    def __init__(self, to, fields_search=(), **kwargs):

        assert 'related_query_name' in kwargs, _(
            'SaplGenericRelation não pode ser instanciada sem '
            'related_query_name.')

        assert fields_search, _(
            'SaplGenericRelation não pode ser instanciada sem fields_search.')

        for field in fields_search:
            # descomente para ver todas os campos que são elementos de busca
            # print(kwargs['related_query_name'], field)

            assert isinstance(field, (tuple, list)), _(
                'fields_search deve ser um array de tuplas ou listas.')

            assert len(field) == 2, _(
                'cada tupla de fields_search deve possuir duas strins')

            # TODO implementar assert para validar campos do Model e lookups

        self.fields_search = fields_search
        super().__init__(to, **kwargs)


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

"""
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

    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.

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

"""


class MateriaPesquisaOrderingFilter(django_filters.OrderingFilter):

    choices = (
        ('', 'Selecione'),
        ('dataC', 'Data, Tipo, Ano, Numero - Ordem Crescente'),
        ('dataD', 'Data, Tipo, Ano, Numero - Ordem Decrescente'),
        ('tipoC', 'Tipo, Ano, Numero, Data - Ordem Crescente'),
        ('tipoD', 'Tipo, Ano, Numero, Data - Ordem Decrescente')
    )
    order_by_mapping = {
        '': [],
        'dataC': ['data_apresentacao', 'tipo__sigla', 'ano', 'numero'],
        'dataD': ['-data_apresentacao', '-tipo__sigla', '-ano', '-numero'],
        'tipoC': ['tipo__sigla', 'ano', 'numero', 'data_apresentacao'],
        'tipoD': ['-tipo__sigla', '-ano', '-numero', '-data_apresentacao'],
    }

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = self.choices
        super(MateriaPesquisaOrderingFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        _value = self.order_by_mapping[value[0]] if value else value
        return super().filter(qs, _value)


class AnoNumeroOrderingFilter(django_filters.OrderingFilter):

    choices = (('', 'Selecione...'),
               ('CRE', 'Ordem Crescente'),
               ('DEC', 'Ordem Decrescente'),)
    order_by_mapping = {
        '': [],
        'CRE': ['ano', 'numero'],
        'DEC': ['-ano', '-numero'],
    }

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = self.choices
        super(AnoNumeroOrderingFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        _value = self.order_by_mapping[value[0]] if value else value
        return super().filter(qs, _value)


def gerar_hash_arquivo(arquivo, pk, block_size=2**20):
    md5 = hashlib.md5()
    arq = open(arquivo, 'rb')
    while True:
        data = arq.read(block_size)
        if not data:
            break
        md5.update(data)
    return 'P' + md5.hexdigest() + '/' + pk


class ChoiceWithoutValidationField(forms.ChoiceField):

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'], code='required')


def models_with_gr_for_model(model):
    return list(map(
        lambda x: x.related_model,
        filter(
            lambda obj: obj.is_relation and
            hasattr(obj, 'field') and
            isinstance(obj, GenericRel),

            model._meta.get_fields(include_hidden=True))
    ))


def generic_relations_for_model(model):
    """
    Esta função retorna uma lista de tuplas de dois elementos, onde o primeiro
    elemento é um model qualquer que implementa SaplGenericRelation (SGR), o
    segundo elemento é uma lista de todas as SGR's que pode haver dentro do
    model retornado na primeira posição da tupla.

    Exemplo: No Sapl, o model Parlamentar tem apenas uma SGR para Autor.
                Se no Sapl existisse apenas essa SGR, o resultado dessa função
                seria:
                    [   #Uma Lista de tuplas
                        (   # cada tupla com dois elementos
                            sapl.parlamentares.models.Parlamentar,
                            [<sapl.utils.SaplGenericRelation: autor>]
                        ),
                    ]
    """
    return list(map(
        lambda x: (x,
                   list(filter(
                       lambda field: (
                           isinstance(
                               field, SaplGenericRelation) and
                           field.related_model == model),
                       x._meta.get_fields(include_hidden=True)))),
        models_with_gr_for_model(model)
    ))


def texto_upload_path(instance, filename, subpath=''):
    """
    O path gerado por essa função leva em conta a pk de instance.
    isso não é possível naturalmente em uma inclusão pois a implementação
    do django framework chama essa função antes do metodo save

    Por outro lado a forma como vinha sendo formada os paths para os arquivos
    são improdutivas e inconsistentes. Exemplo: usava se o valor de __str__
    do model Proposicao que retornava a descrição da proposição, não retorna
    mais, para uma pasta formar o path do texto_original.
    Ora, o resultado do __str__ citado é totalmente impróprio para ser o nome
    de uma pasta.

    Para colocar a pk no path, a solução encontrada foi implementar o método
    save nas classes que possuem atributo do tipo FileField, implementação esta
    que guarda o FileField em uma variável independente e temporária para savar
    o object sem o arquivo e, logo em seguida, salvá-lo novamente com o arquivo
    Ou seja, nas inclusões que já acomparem um arquivo, haverá dois saves,
    um para armazenar toda a informação e recuperar o pk, e outro logo em
    seguida para armazenar o arquivo.
    """

    if subpath and '/' not in subpath:
        subpath = subpath + '/'

    filename = re.sub('[^a-zA-Z0-9.]', '-', filename).strip('-').lower()
    filename = re.sub('[-]+', '-', filename)
    path = './sapl/%(model_name)s/%(pk)s/%(subpath)s%(filename)s' % {
        'model_name': instance._meta.model_name,
        'pk': instance.pk,
        'subpath': subpath,
        'filename': filename}

    return path
