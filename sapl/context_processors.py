
from base.models import CasaLegislativa


# TODO: this need to be cached and retrieved once!!!
def query_database():
    return CasaLegislativa.objects.first()


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

    casa_legislativa = query_database()

    if casa_legislativa:
        context['parliament_type'] = casa_legislativa.nome
        context['city'] = casa_legislativa.municipio
        context['state'] = casa_legislativa.uf
        context['logotipo'] = casa_legislativa.logotipo

    return context
