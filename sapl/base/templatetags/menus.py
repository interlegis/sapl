import logging

from django import template
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
import yaml


register = template.Library()

logger = logging.getLogger(__name__)


@register.inclusion_tag('menus/menu.html', takes_context=True)
def menu(context, path=None):
    return nav_run(context, path)


@register.inclusion_tag('menus/subnav.html', takes_context=True)
def subnav(context, path=None):
    return nav_run(context, path)


@register.inclusion_tag('menus/nav.html', takes_context=True)
def navbar(context, path=None):
    return nav_run(context, path)


def nav_run(context, path=None):
    """Renderiza sub navegação para objetos no padrão Mestre Detalhe

    Existem três possíveis fontes de busca do yaml
    com precedência enumerada abaixo:
        1) Se a variável path não é nula;
        2) Se existe no contexto a chave subnav_template_name;
        3) o path default: <app_name>/subnav.yaml

    Os campos esperados nos arquivos yaml são:
        title
        url
        check_permission - opcional. quando usado
            será realizado o teste de permissão para renderizá-lo.
    """
    menu = None
    root_pk = context.get('root_pk', None)
    if not root_pk:
        obj = context.get('object', None)
        if obj:
            root_pk = obj.pk

    if root_pk or 'subnav_template_name' in context or path:
        request = context['request']

        """
        As implementações das Views de Modelos que são dados auxiliares e
        de diversas app's estão concentradas em urls com prefixo 'sistema'.
        Essas Views não possuem submenu de navegação e são incompativeis com a
        execução deste subnav. Inicialmente, a maneira mais prática encontrada
        de isolar foi com o teste abaixo.
        """

        rm = request.resolver_match
        app_template = rm.app_name.rsplit('.', 1)[-1]

        if path:
            yaml_path = path
        elif 'subnav_template_name' in context:
            yaml_path = context['subnav_template_name']
        else:
            yaml_path = '%s/%s' % (app_template, 'subnav.yaml')

        if not yaml_path:
            return

            """
            Por padrão, são carragados dois Loaders,
            filesystem.Loader - busca em TEMPLATE_DIRS do projeto atual
            app_directories.Loader - busca em todas apps instaladas
            A função nativa abaixo busca em todos os Loaders Configurados.
            """
        try:
            yaml_template = template.loader.get_template(yaml_path)
        except:
            return

        try:
            rendered = yaml_template.template.render(context)
            menu = yaml.load(rendered)
            resolve_urls_inplace(menu, root_pk, rm, context)
        except Exception as e:
            raise Exception(_("""Erro na conversão do yaml %s. App: %s.
                                    Erro:
                                      %s
                                """) % (
                yaml_path, rm.app_name, str(e)))

    return {'menu': menu}


def resolve_urls_inplace(menu, pk, rm, context):
    if isinstance(menu, list):
        list_active = ''
        for item in menu:
            menuactive = resolve_urls_inplace(item, pk, rm, context)
            list_active = menuactive if menuactive else list_active
            if not isinstance(item, list):
                item['active'] = menuactive

        return list_active
    else:
        if 'url' in menu:

            url_name = menu['url']

            if 'check_permission' in menu and not context[
                    'request'].user.has_perm(menu['check_permission']):
                menu['url'] = ''
                menu['active'] = ''
            else:
                if '/' in url_name:
                    pass
                elif ':' in url_name:
                    try:
                        menu['url'] = reverse('%s' % menu['url'])
                    except:
                        try:
                            menu['url'] = reverse('%s' % menu['url'],
                                                  kwargs={'pk': pk})
                        except:
                            # tem que ser root_pk pois quando está sendo
                            # renderizado um detail, update, delete
                            # e ainda sim é necessário colocar o menu,
                            # nestes, casos o pk da url é do detail, e não
                            # do master, porém, os menus do subnav, apontam para
                            # outras áreas que as urls destas são construídas
                            # com pk do master, e não do detail... por isso
                            # no contexto deve ter, ou root_pk, ou object
                            # sendo que qualquer um dos dois,deverá ser o
                            # master.
                            # Estes detalhes são relevantes quando usa-se
                            # o menu isolado. Por outro lado, quando usado
                            # conjuntamente com o crud, este configura o contexto
                            # como se deve para o menus.py
                            log = """
                            Erro na construção do Menu:
                            menu: {}
                            url: {}
                            1) Verifique se a url existe 
                            2) Se existe no contexto um desses itens:
                                - context['root_pk'] pk do master
                                - context['object'] objeto do master
                            """.format(menu['title'], menu['url'])
                            logger.error(log)
                            raise Exception(log)

                else:
                    try:
                        menu['url'] = reverse('%s:%s' % (
                            rm.app_name, menu['url']))
                    except:
                        try:
                            menu['url'] = reverse('%s:%s' % (
                                rm.app_name, menu['url']), kwargs={'pk': pk})
                        except:
                            log = """Erro na construção do Menu:
                            menu: {}
                            url: {}
                            1) Verifique se a url existe 
                            2) Se existe no contexto um desses itens:
                                - context['root_pk'] pk do master
                                - context['object'] objeto do master
                            """.format(menu['title'], menu['url'])
                            logger.error(log)
                            raise Exception(log)

                menu['active'] = 'active'\
                    if context['request'].path == menu['url'] else ''
                if not menu['active']:
                    """
                    Se não encontrada diretamente,
                    procura a url acionada dentro do crud, caso seja um.
                    Serve para manter o active no subnav correto ao acionar
                    as funcionalidades diretas do MasterDetailCrud, como:
                    - visualização de detalhes, adição, edição, remoção.
                    """
                    if 'view' in context:
                        view = context['view']
                        if hasattr(view, '__class__') and\
                                hasattr(view.__class__, 'crud'):
                            urls = view.__class__.crud.get_urls()
                            for u in urls:
                                if (u.name == url_name or
                                        'urls_extras' in menu and
                                        u.name in menu['urls_extras']):
                                    menu['active'] = 'active'
                                    break
        elif 'check_permission' in menu and not context[
                'request'].user.has_perm(menu['check_permission']):
            menu['active'] = ''
            del menu['children']

        if 'children' in menu:
            menu['active'] = resolve_urls_inplace(
                menu['children'], pk, rm, context)
        return menu['active']
