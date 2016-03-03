"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from base.views import get_casalegislativa


def parliament_info(request):

    context = {
        'state': 'Estado',
        'state_abbr': 'UF',
        'city': 'Cidade',
        'parliament_type': 'Câmara Municipal',
        'address': 'Rua Lorem Ipsum de Amet, Casa X',
        'postal_code': '70000-000',
        'phone_number': '00 0000-0000',
        'url_portal': '#',
        'url_email': '#',
    }

    casa_legislativa = get_casalegislativa()

    if casa_legislativa:
        context['parliament_type'] = casa_legislativa.nome
        context['city'] = casa_legislativa.municipio
        context['state'] = casa_legislativa.uf
        context['logotipo'] = casa_legislativa.logotipo

    return context
