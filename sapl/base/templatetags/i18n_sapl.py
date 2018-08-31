from django.templatetags.i18n import *
from django.utils.encoding import force_text
from sapl.translation import sapl_expressions


@register.tag("trans")
def do_translate_sapl(parser, token):
    trans = do_translate(parser, token)
    return sapl_expressions.swap_translate(trans)


@register.tag("blocktrans")
def do_block_translate_sapl(parser, token):
    block_trans = do_block_translate(parser, token)
    return sapl_expressions.swap_block_translate(block_trans)
