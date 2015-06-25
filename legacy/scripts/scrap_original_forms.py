import os
import re
import string
from inspect import getsourcelines

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from field_mappings import field_mappings
from utils import listify


def _read_line(tr):
    for td in tr.find_all('td'):
        label = td.text.strip().split('\n')[0].strip(u'\xa0' + string.whitespace)
        names = [c.attrs['name'] for c in td.children if isinstance(c, Tag) and 'name' in c.attrs]
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
    field_names_to_old = field_mappings[model]
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
    source = getsourcelines(model)[0]
    title, labels, non_matched = extract_verbose_names(model)

    field_regex = ' *(.+) = (models\..*)\((.*)\)'
    new_lines = []
    for line in source[1:]:
        for regex, split in [
                (field_regex + ' *# (.+)', lambda groups: groups),
                (field_regex, lambda groups: groups + [''])]:
            match = re.match(regex, line)
            if match:
                name, path, args, legacy_name = split(match.groups())
                if name in labels:
                    args = [args] if args.strip() else []
                    args.append("verbose_name=_(u'%s')" % labels[name])
                    args = ', '.join(args)
                new_lines.append(
                    ('    %s = %s(%s)' % (name, path, args), legacy_name))
                break
        else:
            new_lines.append((line, ''))
    yield source[0].rstrip()
    cols = max(map(len, [line for line, _ in new_lines]))
    for line, legacy_name in new_lines:
        line = line.rstrip().ljust(cols)
        if legacy_name:
            yield line + ' # ' + legacy_name
        else:
            yield line
    if title:
        if title.endswith('s'):
            title_singular, title_plural = '', title
        else:
            title_singular, title_plural = title, ''
        yield """
    class Meta:
        verbose_name = _(u'%s')
        verbose_name_plural = _(u'%s')
""" % (title_singular, title_plural)

