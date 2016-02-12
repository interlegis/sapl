import os

import yaml
from django import template
from django.core.urlresolvers import reverse

from sapl.settings import BASE_DIR

register = template.Library()
TEMPLATES_DIR = BASE_DIR.child("templates")


@register.inclusion_tag('menus/subnav.html', takes_context=True)
def subnav(context, path=None):
    """Renders a subnavigation for views of a certain object.

    If not provided, path defaults to <app_name>/subnav.yaml
    """
    # TODO: 118n !!!!!!!!!!!!!!
    # How to internationalize yaml files????
    menu = None
    if 'object' in context:
        obj = context['object']
        default_path = '%s/subnav.yaml' % obj.__class__._meta.app_label
        path = os.path.join(TEMPLATES_DIR, path or default_path)
        if os.path.exists(path):
            menu = yaml.load(open(path, 'r'))
            resolve_urls_inplace(menu, obj.pk)
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
