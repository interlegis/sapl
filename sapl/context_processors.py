from django.contrib import messages

def parliament_info(request):

    return {
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
