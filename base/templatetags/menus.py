from os.path import dirname

import yaml
from django import template
from django.core.urlresolvers import reverse
from sapl.settings import BASE_DIR

register = template.Library()
TEMPLATES_DIR = BASE_DIR.child("templates")


@register.inclusion_tag('menus/subnav.html', takes_context=True)
def subnav(context, path):
    yaml_filename = TEMPLATES_DIR.child(*path.split('/'))
    menu = yaml.load(open(yaml_filename, 'r'))
    resolve_urls_inplace(menu, context['object'].pk)
    return dict(menu=menu)


def resolve_urls_inplace(menu, pk):
    if isinstance(menu, list):
        for item in menu:
            resolve_urls_inplace(item, pk)
    else:
        if 'url' in menu:
            menu['url'] = reverse(menu['url'], kwargs={'pk': pk})
        if 'children' in menu:
            resolve_urls_inplace(menu['children'], pk)
