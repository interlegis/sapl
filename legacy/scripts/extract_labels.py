import string
from bs4 import BeautifulSoup
from itertools import chain


def _label_from_td(td):
    return td.text.strip().split('\n')[0].strip(u'\xa0' + string.whitespace)


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

