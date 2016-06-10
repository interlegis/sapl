

from sapl.base.views import get_casalegislativa


def parliament_info(request):
    casa = get_casalegislativa()
    if casa:
        return casa.__dict__
    else:
        return {}
