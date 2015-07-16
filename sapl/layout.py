from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Submit, Reset, Layout, Div, Fieldset
from django.utils.translation import ugettext as _


def to_column(name_span):
    try:
        fieldname, span = name_span
    except:
        return name_span
    else:
        return Div(fieldname, css_class='col-xs-%d' % span)


def to_row(names_spans):
    return Div(*list(map(to_column, names_spans)), css_class='row-fluid')


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
        _fields = list(to_fieldsets(fields)) + [
            FormActions(
                Submit('save', _('Save'), css_class='btn btn-primary '),
                Reset('reset', _('Cancel'), css_class='btn'))
        ]
        super(SaplFormLayout, self).__init__(*_fields)
