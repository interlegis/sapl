from crispy_forms_foundation.layout import (
    Div, Layout, Fieldset, Row, Column, Submit, HTML)
from django.utils.translation import ugettext as _


def to_column(name_span):
    fieldname, span = name_span
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
        buttons = Div(
            HTML('<a href="{{ view.cancel_url }}"'
                 ' class="button radius alert">%s</a>' % _('Cancelar')),
            Submit('submit', _('Enviar'),
                   css_class='button radius success right'),
            css_class='radius clearfix'
        )
        _fields = list(to_fieldsets(fields)) + \
            [Row(Column(buttons, css_class='clearfix'))]
        super(SaplFormLayout, self).__init__(*_fields)
