from crispy_forms_foundation.layout import (
    Div, Layout, Fieldset, Row, Column, Button, Submit)
from django.utils.translation import ugettext as _


def to_column(name_span):
    try:
        fieldname, span = name_span
    except:
        return name_span
    else:
        return Column(fieldname, css_class='large-%d' % span)


def to_row(names_spans):
    return Row(*list(map(to_column, names_spans)))


def to_fieldsets(fields):
    for field in fields:
        if isinstance(field, list):
            legend, *row_specs = field
            rows = [to_row(name_span_list) for name_span_list in row_specs]
            yield Fieldset(legend, *rows)
        else:
            yield field


class SaplFormLayout(Layout):

    def __init__(self, *fields):
        _fields = list(to_fieldsets(fields)) + buttons_crispies()
        super(SaplFormLayout, self).__init__(*_fields)


def buttons_crispies():
    return [
        Row(
            Column(
                Div(
                    Submit('submit', _('Enviar'),
                           css_class='button radius success right'),
                    Button('cancel', _('Cancelar'),
                           css_class='button radius alert left'),
                    css_class='radius clearfix'
                ),
                css_class='clearfix'
            ),
        ),
    ]
