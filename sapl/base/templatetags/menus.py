from django import template
from django.core.urlresolvers import reverse
import yaml


register = template.Library()


@register.inclusion_tag('menus/subnav.html', takes_context=True)
def subnav(context, path=None):
    """Renderiza sub navegação para objetos no padrão Mestre Detalhe

    Existem três possíveis fontes de busca do yaml
    com precedência enumerada abaixo:
        1) Se a variável path não é nula;
        2) Se existe no contexto a chave subnav_template_name;
        3) o path default: <app_name>/subnav.yaml
    """
    menu = None
    root_pk = context.get('root_pk', None)
    if not root_pk:
        obj = context.get('object', None)
        if obj:
            root_pk = obj.pk

    if root_pk:
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

        try:
            """
            Por padrão, são carragados dois Loaders,
            filesystem.Loader - busca em TEMPLATE_DIRS do projeto atual
            app_directories.Loader - busca em todas apps instaladas
            A função nativa abaixo busca em todos os Loaders Configurados.
            """
            yaml_template = template.loader.get_template(yaml_path)
            rendered = yaml_template.render()
            menu = yaml.load(rendered)
            resolve_urls_inplace(menu, root_pk, rm, context)
        except Exception as e:
            print(e)

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
            menu['url'] = reverse('%s:%s' % (rm.app_name, menu['url']),
                                  kwargs={'pk': pk})
            menu['active'] = 'active'\
                if context['request'].path == menu['url'] else ''

            if not menu['active']:
                """
                Se não encontrada diretamente,
                procura a url acionada dentro do crud, caso seja um.
                Serve para manter o active no suvnav correto ao acionar
                as funcionalidades diretas do MasterDetailCrud, como:
                - visualização de detalhes, adição, edição, remoção.

                Casos para urls_extras:
                Em relações de segundo nível, como ocorre em
                (0) Comissões -> (1) Composição -> (2) Participação

                (2) não tem ligação direta com (1) através da view. Para (2)
                ser localizado, e o nav-tabs ou nav-pills do front-end serem
                ativados foi inserido o teste de existência de urls_extras
                para serem testadas e, sendo válidado, o active do front-end
                seja devidamente colocado.
                """

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

        if 'children' in menu:
            menu['active'] = resolve_urls_inplace(
                menu['children'], pk, rm, context)
        return menu['active']
