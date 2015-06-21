import os
import string
from difflib import SequenceMatcher
from itertools import chain

from bs4 import BeautifulSoup
from django.template.defaultfilters import slugify

from materia.models import MateriaLegislativa
from bs4.element import NavigableString, Tag


def _label_from_td(td):
    return td.text.strip().split('\n')[0].strip(u'\xa0' + string.whitespace)


# TODO: improve, getting ids inputs
# TODO: improve, getting fieldsets
def get_fieldsets(filename):
    """Extract labels from a file containg the html source of a rendered
    legacy sapl form
    """
    with open(filename, 'r') as f:
        cont = f.read()
    html_doc = cont.decode('utf-8')
    soup = BeautifulSoup(html_doc, 'html.parser')
    forms = soup.find_all('form')
    [form] = [f for f in forms if (u'method', u'post') in f.attrs.items()]

    # children are either tags or strings...
    assert set(type(c) for c in form.children) == {Tag, NavigableString}
    # ... and all strings are empty
    assert all(not c.strip() for c in form.children if isinstance(c, NavigableString))

    for fieldset in form.find_all('fieldset'):
        legend = fieldset.find('legend').text
        yield dict(
            legend=legend,
            lines=[[_label_from_td(td) for td in tr.find_all('td')]
                   for tr in fieldset.find_all('tr')]
        )


def get_labels(fieldsets):
    for fieldset in fieldsets:
        for line in fieldset['lines']:
            for label in line:
                yield label


def print_fieldsets(fieldsets):
    for fieldset in fieldsets:
        print fieldset['legend']
        for line in fieldset['lines']:
            print '  ' + ', '.join(line)


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio() > 0.6

model = MateriaLegislativa
filename = os.path.join(os.path.dirname(__file__),
                        'original_forms/%s.html' % model.__name__)
fieldsets = list(get_fieldsets(filename))
labels = get_labels(fieldsets)
slugs_to_labels = [(slugify(s.lower()).replace('-', '_'), s) for s in labels]
field_names = [f.name for f in model._meta.fields if f.name != 'id']

matches = {}

while field_names:
    percent, field, slug, label = sorted(
        [(similar(a, slug), a, slug, label)
         for a in field_names
         for (slug, label) in slugs_to_labels])[-1]
    if percent > 0.6:
        matches[field] = (label, percent)
        slugs_to_labels.remove((slug, label))
    else:
        print 'Label not found for [%s]' % field
    field_names.remove(field)
