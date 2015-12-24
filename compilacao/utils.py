from crispy_forms_foundation.layout import (HTML, Column, Div, Fieldset,
                                            Layout, Row, Submit)
from django.apps import apps
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


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


def make_choices(*choice_pairs):
    assert len(choice_pairs) % 2 == 0
    ipairs = iter(choice_pairs)
    choices = list(zip(ipairs, ipairs))
    yield choices
    for key, value in choices:
        yield key

YES_NO_CHOICES = [(True, _('Sim')), (False, _('Não'))]


def int_to_roman(int_value):
    # if isinstance(int_value, type(1)):
    #    raise TypeError("expected integer, got %s" % type(int_value))
    if not 0 < int_value < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC',
            'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = ""
    for i in range(len(ints)):
        count = int(int_value / ints[i])
        result += nums[i] * count
        int_value -= ints[i] * count
    return result


def int_to_letter(int_value):
    result = ''
    int_value -= 1
    while int_value >= 26:
        rest = int_value % 26
        int_value = int(int_value / 26) - 1
        result = chr(rest + 65) + result
    result = chr(int_value + 65) + result
    return result


def from_to(start, end):
    return list(range(start, end + 1))


def make_pagination(index, num_pages):
    '''Make a list of adjacent page ranges interspersed with "None"s

    The list starts with [1, 2] and end with [num_pages-1, num_pages].
    The list includes [index-1, index, index+1]
    "None"s separate those ranges and mean ellipsis (...)

    Example:  [1, 2, None, 10, 11, 12, None, 29, 30]
    '''

    PAGINATION_LENGTH = 10
    if num_pages <= PAGINATION_LENGTH:
        return from_to(1, num_pages)
    else:
        if index - 1 <= 5:
            tail = [num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - 3)
        else:
            if index + 1 >= num_pages - 3:
                tail = from_to(index - 1, num_pages)
            else:
                tail = [index - 1, index, index + 1,
                        None, num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - len(tail) - 1)
        return head + [None] + tail
