# -*- coding: utf-8 -*-
import os
import re
import string

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from field_renames import field_renames
from migration import appconfs
from utils import listify, getsourcelines


assert appconfs  # to prevent removal by automatic organize imports on this file


def _read_line(tr):
    for td in tr.find_all('td'):
        label = td.text.strip().split('\n')[0].strip(u'\xa0' + string.whitespace)
        if label.endswith('(*)'):
            label = label[:-3].strip()
        names = [c.attrs['name'] for c in td.findAll() if isinstance(c, Tag) and 'name' in c.attrs]
        if names:
            name = names[0].split('_', 1)[-1]
            yield name, label


def extract_title_and_fieldsets(model):
    filename = os.path.join(os.path.dirname(__file__),
                            'original_forms/%s.html' % model.__name__)
    try:
        with open(filename, 'r') as f:
            cont = f.read()
    except IOError:
        return None, []

    html_doc = cont.decode('utf-8')
    soup = BeautifulSoup(html_doc, 'html.parser')
    forms = soup.find_all('form')
    [form] = [f for f in forms if (u'method', u'post') in f.attrs.items()]
    # children are either tags or strings...
    assert set(type(c) for c in form.children) == {Tag, NavigableString}
    # ... and all strings are empty
    assert all(not c.strip() for c in form.children if isinstance(c, NavigableString))

    title = soup.find('h1', {'class': 'firstHeading'})
    title = title.text.strip() if title else None
    fieldsets = [dict(
        legend=fieldset.find('legend').text if fieldset.find('legend') else '',
        lines=[list(_read_line(tr)) for tr in fieldset.find_all('tr')])
        for fieldset in form.find_all('fieldset')]

    return title, fieldsets


def get_names_labels(fieldsets):
    for fieldset in fieldsets:
        for line in fieldset['lines']:
            for name, label in line:
                yield name, label


def print_title_and_fieldsets(model):
    title, fieldsets = extract_title_and_fieldsets(model)
    print '#### %s ####\n' % title
    for fieldset in fieldsets:
        print fieldset['legend']
        for line in fieldset['lines']:
            print '  ' + ' | '.join('%s : %s' % (id, label) for id, label in line)


def extract_verbose_names(model):
    title, fieldsets = extract_title_and_fieldsets(model)
    names_to_labels = dict(get_names_labels(fieldsets))

    field_names = [f.name for f in model._meta.fields if f.name != 'id']

    labels = {}
    field_names_to_old = field_renames[model]
    for name in field_names:
        old_name = field_names_to_old[name]
        label = names_to_labels.get(old_name, None)
        if label:
            labels[name] = label
            del names_to_labels[old_name]
    for name, label in labels.items():
        field_names.remove(name)
    non_matched = field_names, names_to_labels
    return title, labels, non_matched


@listify
def source_with_verbose_names(model):
    source = getsourcelines(model)
    title, labels, non_matched = extract_verbose_names(model)

    field_regex = ' *(.+) = (models\.[^\(]*)\((.*verbose_name=_\(.*\)|.*)\)'
    new_lines = []
    class_meta_already_exists = False
    for line in source[1:]:
        for regex, split in [
                (field_regex + ' *# (.+)', lambda groups: groups),
                (field_regex, lambda groups: groups + ('',))]:
            match = re.match(regex, line)
            if match:
                name, path, args, legacy_name = split(match.groups())
                if name in labels and 'verbose_name' not in args:
                    args = [args] if args.strip() else []
                    args.append(u"verbose_name=_(u'%s')" % labels[name])
                    args = u', '.join(args)
                new_lines.append(
                    (u'    %s = %s(%s)' % (name, path, args), legacy_name))
                break
        else:
            if 'class Meta:' in line:
                class_meta_already_exists = True
            new_lines.append((line, ''))
    yield source[0].rstrip()
    cols = max(map(len, [line for line, _ in new_lines]))
    for line, legacy_name in new_lines:
        line = line.rstrip().ljust(cols)
        if legacy_name:
            yield line + '  # ' + legacy_name
        else:
            yield line

    # class Meta
    if class_meta_already_exists:
        return

    if title == 'Tabelas Auxiliares':
        title = ''
    title = title if title else ''

    def add_s(name):
        return ' '.join(p if p.endswith('s') else p + 's' for p in name.split())

    def remove_s(name):
        return ' '.join(p[:-1] if p.endswith('s') else p for p in name.split())

    if not title:
        # default title from model name
        title_singular = u' '.join(re.findall('[A-Z][^A-Z]*', model.__name__))
        title_singular = re.sub('cao\\b', u'ção', title_singular)
        title_singular = re.sub('ao\\b', u'ão', title_singular)
        title_plural = add_s(title_singular.replace(u'ção', u'ções').replace(u'ão', u'ões'))

    elif title.endswith('s'):
        title_singular = remove_s(title.replace(u'ções', u'ção').replace(u'ões', u'ão'))
        title_plural = title
    else:
        title_singular = title
        title_plural = add_s(title.replace(u'ção', u'ções').replace(u'ão', u'ões'))

    yield """
    class Meta:
        verbose_name = _(u'%s')
        verbose_name_plural = _(u'%s')""" % (title_singular, title_plural)


def print_app_with_verbose_names(app):
    print '##################################################################'
    header = '# -*- coding: utf-8 -*-\n'
    for line in getsourcelines(app.models_module):
        if line in ['# -*- coding: utf-8 -*-',
                    'from django.utils.translation import ugettext as _', ]:
            continue
        elif line == 'from django.db import models':
            header += '''from django.db import models
from django.utils.translation import ugettext as _
'''
        elif 'class' in line:
            break
        else:
            header += line + '\n'
    print header.strip()
    for model in app.models.values():
        print '\n'
        for p in source_with_verbose_names(model):
            print p


def list_models_with_no_scrapped_data(app):
    for model in app.models.values():
        if not any(extract_verbose_names(model)[:2]):
            print model.__name__
