import os
import string
from difflib import SequenceMatcher
from itertools import chain

from bs4 import BeautifulSoup
from django.template.defaultfilters import slugify

from materia.models import MateriaLegislativa


def _label_from_td(td):
    return td.text.strip().split('\n')[0].strip(u'\xa0' + string.whitespace)


# TODO: improve, getting ids inputs
# TODO: improve, getting fieldsets
def get_labels(filename, flat=True):
    """Extract labels from a file containg the html source of a rendered
    legacy sapl form
    """
    with open(filename, 'r') as f:
        cont = f.read()
    html_doc = cont.decode('utf-8')
    soup = BeautifulSoup(html_doc, 'html.parser')
    forms = soup.find_all('form')
    [form] = [f for f in forms if (u'method', u'post') in f.attrs.items()]

    labels = [[_label_from_td(td) for td in tr.find_all('td')] for tr in form.find_all('tr')]
    for line in labels:
        print ', '.join("u'%s'" % l for l in line)
    if flat:
        return list(chain(*labels))
    else:
        return labels


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio() > 0.6

model = MateriaLegislativa
filename = os.path.join(os.path.dirname(__file__),
                        'original_forms/%s.html' % model.__name__)
labels = get_labels(filename)
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
