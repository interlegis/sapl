from math import ceil

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Fieldset, Layout, Submit
from django import template
from django.urls import reverse, reverse_lazy
from django.utils import formats
from django.utils.translation import ugettext as _
import rtyaml


def heads_and_tails(list_of_lists):
    for alist in list_of_lists:
        yield alist[0], alist[1:]


def to_column(name_span):
    fieldname, span = name_span
    return Div(fieldname, css_class='col-md-%d' % span)


def to_row(names_spans):
    return Div(*map(to_column, names_spans), css_class='row')


def to_fieldsets(fields):
    for field in fields:
        if isinstance(field, list):
            legend, row_specs = field[0], field[1:]
            rows = [to_row(name_span_list) for name_span_list in row_specs]
            yield Fieldset(legend, *rows)
        else:
            yield field


def form_actions(more=[Div(css_class='clearfix')],
                 label=_('Salvar'), name='salvar',
                 css_class='float-right', disabled=True):

    if disabled:
        doubleclick = 'this.form.submit();this.disabled=true;'
    else:
        doubleclick = 'return true;'

    return FormActions(
        *more,
        Submit(name, label, css_class=css_class,
               # para impedir resubmissão do form
               onclick=doubleclick),
        css_class='form-group row justify-content-between'
    )


class SaplFormHelper(FormHelper):
    render_hidden_fields = True  # default = False
    """
    até a release 1.6.1 do django-crispy-forms, os fields em Meta.Fields eram
    renderizados mesmo se não mencionados no helper.
    Com esta mudança (https://github.com/django-crispy-forms/django-crispy-forms/commit/6b93e8a362422db8fe54aa731319c7cbc39990ba)
    render_hidden_fields foi adicionado uma condição em que a cada
    instância do Helper, fosse decidido se os fields não mencionados serião ou
    não renderizados...
    O Sapl até este commit: https://github.com/interlegis/sapl/commit/22b87f36ebc8659a6ecaf8831ab0f425206b0993
    utilizou o django-crispy-forms na versão 1.6.1, ou seja,
    sem a condição render_hidden_fields o que fazia o FormHelper, na 1.6.1
    set comportar como se, agora, na 1.7.2 o default fosse True.
    Como todos os Forms do Sapl foram construídos assumindo que fields
    não incluídos explicitamente no Helper, o helper o incluiria implicitamente,
    e assim o era, de acordo com commit acima do django-crispy-forms, então
    cria-se essa classe:

        class SaplFormHelper(FormHelper):
            render_hidden_fields = True

    onde torna o default, antes False, agora = True, o esperado pelos forms do sapl,
    e substituí-se todos os FormHelper por SaplFormHelper dentro do projeto Sapl


    esta explicação ficará aqui dentro do código, via commit, e na issue #2456.
    """


class SaplFormLayout(Layout):

    def __init__(self, *fields, cancel_label=_('Cancelar'),
                 save_label=_('Salvar'), actions=None):

        buttons = actions
        if not buttons:
            buttons = form_actions(label=save_label, more=[
                HTML('<a href="{{ view.cancel_url }}"'
                     ' class="btn btn-dark">%s</a>' % cancel_label)
                if cancel_label else None])

        _fields = list(to_fieldsets(fields))
        if buttons:
            _fields += [to_row([(buttons, 12)])]
        super(SaplFormLayout, self).__init__(*_fields)


def get_field_display(obj, fieldname):
    field = ''
    try:
        field = obj._meta.get_field(fieldname)
    except Exception as e:
        """ nos casos que o fieldname não é um field_model,
            ele pode ser um aggregate, annotate, um property, um manager,
            ou mesmo uma método no model.
        """
        value = getattr(obj, fieldname)
        try:
            verbose_name = value.model._meta.verbose_name
        except AttributeError:
            verbose_name = ''

    else:
        verbose_name = str(field.verbose_name)\
            if hasattr(field, 'verbose_name') else ''

        if hasattr(field, 'choices') and field.choices:
            value = getattr(obj, 'get_%s_display' % fieldname)()
        else:
            value = getattr(obj, fieldname)

    str_type_from_value = str(type(value))
    str_type_from_field = str(type(field))

    if value is None:
        display = ''
    elif '.date' in str_type_from_value:
        display = formats.date_format(value, "SHORT_DATE_FORMAT")
    elif 'bool' in str_type_from_value:
        display = _('Sim') if value else _('Não')
    elif 'ImageFieldFile' in str(type(value)):
        if value:
            display = '<img src="{}" />'.format(value.url)
        else:
            display = ''
    elif 'FieldFile' in str_type_from_value:
        if value:
            display = '<a href="{}">{}</a>'.format(
                value.url,
                value.name.split('/')[-1:][0])
        else:
            display = ''
    elif 'ManyRelatedManager' in str_type_from_value\
            or 'RelatedManager' in str_type_from_value\
            or 'GenericRelatedObjectManager' in str_type_from_value:
        display = '<ul>'
        for v in value.all():
            display += '<li>%s</li>' % str(v)
        display += '</ul>'
        if not verbose_name:
            if hasattr(field, 'related_model'):
                verbose_name = str(
                    field.related_model._meta.verbose_name_plural)
            elif hasattr(field, 'model'):
                verbose_name = str(field.model._meta.verbose_name_plural)
    elif 'GenericForeignKey' in str_type_from_field:
        display = '<a href="{}">{}</a>'.format(
            reverse(
                '%s:%s_detail' % (
                    value._meta.app_config.name, obj.content_type.model),
                args=(value.id,)),
            value)
    elif 'TextField' in str_type_from_field:
        display = value.replace('\n', '<br/>')
        display = '<div class="dont-break-out">{}</div>'.format(display)
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

    @property
    def layout_key_set(self):
        if hasattr(super(CrispyLayoutFormMixin, self), 'layout_key_set'):
            return super(CrispyLayoutFormMixin, self).layout_key_set
        else:
            obj = self.crud if hasattr(self, 'crud') else self
            return getattr(obj.model,
                           obj.model_set).field.model.__name__

    def get_layout(self):
        yaml_layout = '%s/layouts.yaml' % self.model._meta.app_config.label
        return read_layout_from_yaml(yaml_layout, self.layout_key)

    def get_layout_set(self):
        obj = self.crud if hasattr(self, 'crud') else self
        yaml_layout = '%s/layouts.yaml' % getattr(
            obj.model, obj.model_set).field.model._meta.app_config.label
        return read_layout_from_yaml(yaml_layout, self.layout_key_set)

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
            if self.layout_key:
                form.helper = SaplFormHelper()
                layout = self.get_layout()

                form.helper.layout = SaplFormLayout(*layout)

            return form

    @property
    def list_field_names(self):
        '''The list of field names to display on table

        This base implementation returns the field names
        in the first fieldset of the layout.
        '''
        obj = self.crud if hasattr(self, 'crud') else self
        if hasattr(obj, 'list_field_names') and obj.list_field_names:
            return obj.list_field_names
        rows = self.get_layout()[0][1:]
        return [fieldname for row in rows for fieldname, __ in row]

    @property
    def list_field_names_set(self):
        '''The list of field names to display on table

        This base implementation returns the field names
        in the first fieldset of the layout.
        '''
        rows = self.get_layout_set()[0][1:]
        return [fieldname for row in rows for fieldname, __ in row]

    def get_column(self, fieldname, span):
        obj = self.get_object()

        func = None
        if '|' in fieldname:
            fieldname, func = tuple(fieldname.split('|'))

        if func:
            verbose_name, text = getattr(self, func)(obj, fieldname)
        else:
            hook_fieldname = 'hook_%s' % fieldname
            if hasattr(self, hook_fieldname):
                verbose_name, text = getattr(
                    self, hook_fieldname)(obj)
            else:
                verbose_name, text = get_field_display(obj, fieldname)

        return {
            'id': fieldname,
            'span': span,
            'verbose_name': verbose_name,
            'text': text,
        }

    def fk_urlize_for_detail(self, obj, fieldname):

        field = obj._meta.get_field(fieldname)
        value = getattr(obj, fieldname)

        display = '<a href="{}">{}</a>'.format(
            reverse(
                '%s:%s_detail' % (
                    value._meta.app_config.name, value._meta.model_name),
                args=(value.id,)),
            value)

        return field.verbose_name, display

    def m2m_urlize_for_detail(self, obj, fieldname):

        manager, fieldname = tuple(fieldname.split('__'))

        manager = getattr(obj, manager)

        verbose_name = manager.model._meta.verbose_name
        display = ''
        for item in manager.all():
            obj_m2m = getattr(item, fieldname)

            if obj == obj_m2m:
                continue

            verbose_name = item._meta.get_field(fieldname).verbose_name

            display += '<li><a href="{}">{}</a></li>'.format(
                reverse(
                    '%s:%s_detail' % (
                        obj_m2m._meta.app_config.name, obj_m2m._meta.model_name),
                    args=(obj_m2m.id,)),
                obj_m2m)

        display += ''

        if display:
            display = '<ul>%s</ul>' % display
        else:
            verbose_name = ''

        return verbose_name, display

    @property
    def layout_display(self):

        return [
            {'legend': legend,
             'rows': [[self.get_column(fieldname, span)
                       for fieldname, span in row]
                      for row in rows]
             } for legend, rows in heads_and_tails(self.get_layout())]


def read_yaml_from_file(yaml_layout):
    from django.utils.safestring import SafeText

    # TODO cache this at application level
    t = template.loader.get_template(yaml_layout)
    # aqui é importante converter para str pois, dependendo do ambiente,
    # o rtyaml pode usar yaml.CSafeLoader, que exige str ou stream

    rendered = str(t.render())
    # Força conversão para string caso seja SafeText.
    if isinstance(rendered, SafeText):
        rendered = rendered.strip()

    return rtyaml.load(rendered)


def read_layout_from_yaml(yaml_layout, key):
    # TODO cache this at application level
    yaml = read_yaml_from_file(yaml_layout)
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
