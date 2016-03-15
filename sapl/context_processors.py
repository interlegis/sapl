
from base.views import get_casalegislativa


def parliament_info(request):

    context = {
        'state': 'Estado não cadastrado.',
        'state_abbr': 'UF não cadastrada.',
        'city': '',
        'parliament_type': 'Nome da câmara não cadastrado.',
        'address': 'Endereço não cadastrado.',
        'postal_code': 'Não cadastrado.',
        'phone_number': 'Não cadastrado.',
        'url_portal': '',
        'url_email': '',
    }

    casa_legislativa = get_casalegislativa()

    if casa_legislativa:
        context['parliament_type'] = casa_legislativa.nome
        context['city'] = casa_legislativa.municipio
        context['state'] = casa_legislativa.uf
        context['logotipo'] = casa_legislativa.logotipo
        context['url_portal'] = casa_legislativa.endereco_web
        context['url_email'] = casa_legislativa.email
        context['state'] = casa_legislativa.uf
        context['state_abbr'] = casa_legislativa.uf
        context['address'] = casa_legislativa.endereco
        context['postal_code'] = casa_legislativa.cep
        context['phone_number'] = casa_legislativa.telefone
    return context
