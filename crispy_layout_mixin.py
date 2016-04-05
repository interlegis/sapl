from math import ceil
from os.path import dirname, join

import rtyaml
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Fieldset, Layout, Submit
from django.utils.translation import ugettext as _


def heads_and_tails(list_of_lists):
    for alist in list_of_lists:
        yield alist[0], alist[1:]


def to_column(name_span):
    fieldname, span = name_span
    return Div(fieldname, css_class='col-md-%d' % span)


def to_row(names_spans):
    return Div(*map(to_column, names_spans), css_class='row-fluid')


def to_fieldsets(fields):
    for field in fields:
        if isinstance(field, list):
            legend, row_specs = field[0], field[1:]
            rows = [to_row(name_span_list) for name_span_list in row_specs]
            yield Fieldset(legend, *rows)
        else:
            yield field


def form_actions(more=[], save_label=_('Salvar')):
    return FormActions(
        Submit('salvar', save_label, css_class='pull-right'), *more)


class SaplFormLayout(Layout):

    def __init__(self, *fields):
        buttons = form_actions(more=[
            HTML('<a href="{{ view.cancel_url }}"'
                 ' class="btn btn-inverse">%s</a>' % _('Cancelar'))])
        _fields = list(to_fieldsets(fields)) + [to_row([(buttons, 12)])]
        super(SaplFormLayout, self).__init__(*_fields)


def get_field_display(obj, fieldname):
    field = obj._meta.get_field(fieldname)
    verbose_name = str(field.verbose_name)
    if field.choices:
        value = getattr(obj, 'get_%s_display' % fieldname)()
    else:
        value = getattr(obj, fieldname)
    if value is None:
        display = ''
    elif 'date' in str(type(value)):
        display = value.strftime("%d/%m/%Y")  # TODO: localize
    elif 'bool' in str(type(value)):
        display = 'Sim' if value else 'Não'
    else:
        display = str(value)
    return verbose_name, display


class CrispyLayoutFormMixin:

    @property
    def layout_key(self):
        if hasattr(super(CrispyLayoutFormMixin, self), 'layout_key'):
            return super(CrispyLayoutFormMixin, self).layout_key
        else:
            return self.model.__name__

    def get_layout(self):
        filename = join(
            dirname(self.model._meta.app_config.models_module.__file__),
            'layouts.yaml')
        return read_layout_from_yaml(filename, self.layout_key)

    @property
    def fields(self):
        if hasattr(self, 'form_class') and self.form_class:
            return None
        else:
            '''Returns all fields in the layout'''
            return [fieldname for legend_rows in self.get_layout()
                    for row in legend_rows[1:]
                    for fieldname, span in row]

    def get_form(self, form_class=None):
        try:
            form = super(CrispyLayoutFormMixin, self).get_form(form_class)
        except AttributeError:
            # simply return None if there is no get_form on super
            pass
        else:
            form.helper = FormHelper()
            form.helper.layout = SaplFormLayout(*self.get_layout())
            return form

    @property
    def list_field_names(self):
        '''The list of field names to display on table

        This base implementation returns the field names
        in the first fieldset of the layout.
        '''
        rows = self.get_layout()[0][1:]
        return [fieldname for row in rows for fieldname, __ in row]

    def get_column(self, fieldname, span):
        obj = self.get_object()
        verbose_name, text = get_field_display(obj, fieldname)
        return {
            'id': fieldname,
            'span': span,
            'verbose_name': verbose_name,
            'text': text,
        }

    @property
    def layout_display(self):

        return [
            {'legend': legend,
             'rows': [[self.get_column(fieldname, span)
                       for fieldname, span in row]
                      for row in rows]
             } for legend, rows in heads_and_tails(self.get_layout())]


def read_yaml_from_file(filename):
    # TODO cache this at application level
    with open(filename, 'r') as yamlfile:
        return rtyaml.load(yamlfile)


def read_layout_from_yaml(filename, key):
    # TODO cache this at application level
    yaml = read_yaml_from_file(filename)
    base = yaml[key]

    def line_to_namespans(line):
        split = [cell.split(':') for cell in line.split()]
        namespans = [[s[0], int(s[1]) if len(s) > 1 else 0] for s in split]
        remaining = 12 - sum(s for n, s in namespans)
        nondefined = [ns for ns in namespans if not ns[1]]
        while nondefined:
            span = ceil(remaining / len(nondefined))
            namespan = nondefined.pop(0)
            namespan[1] = span
            remaining = remaining - span
        return list(map(tuple, namespans))

    return [[legend] + [line_to_namespans(l) for l in lines]
            for legend, lines in base.items()]
