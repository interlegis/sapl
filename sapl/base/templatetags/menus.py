import os

from django import template
from django.core.urlresolvers import reverse
import yaml


register = template.Library()


@register.inclusion_tag('menus/subnav.html', takes_context=True)
def subnav(context, path=None):
    """Renders a subnavigation for views of a certain object.

    If not provided, path defaults to <app_name>/subnav.yaml
    """
    # TODO: 118n !!!!!!!!!!!!!!
    # How to internationalize yaml files????
    menu = None
    root_pk = context.get('root_pk', None)
    if not root_pk:
        obj = context.get('object', None)
        if obj:
            root_pk = obj.pk

    if root_pk:
        request = context['request']

        if 'sistema' in request.path:
            return

        app = request.resolver_match.app_name
        app_template = app.split('.')
        app_template = app_template[1] if app_template[
            0] == 'sapl' and len(app_template) > 1 else app_template[0]

        yaml_path = '%s/subnav.yaml' % app_template

        try:
            """ Por padrão, são carragados dois Loaders,  
            filesystem.Loader - busca em TEMPLATES_DIRS do projeto atual
            app_directories.Loader - busca em todas apps instaladas
            A função abaixo é nativa e busca em todos os Loaders Configurados.
            """
            yaml_template = template.loader.get_template(yaml_path)
            menu = yaml.load(open(yaml_template.origin.name, 'r'))
            resolve_urls_inplace(menu, root_pk, app)
        except:
            # um erro será lançado por get_template se não for encontrado
            # yaml_path em nenhum de locais registrados.
            pass

    return {'menu': menu}


def resolve_urls_inplace(menu, pk, app):
    if isinstance(menu, list):
        for item in menu:
            resolve_urls_inplace(item, pk, app)
    else:
        if 'url' in menu:
            menu['url'] = reverse('%s:%s' % (app, menu['url']),
                                  kwargs={'pk': pk})
        if 'children' in menu:
            resolve_urls_inplace(menu['children'], pk, app)
