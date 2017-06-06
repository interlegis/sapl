from django.utils.translation import ugettext as _


class UnknownUrlNameError(Exception):

    def __init__(self, url_name):
        self.url_name = url_name

    def __str__(self):
        return repr(
                _("Funcionalidade")
                + " '%s' " % (self.url_name)
                + _("pode ter sido removida ou movida para outra url."))
