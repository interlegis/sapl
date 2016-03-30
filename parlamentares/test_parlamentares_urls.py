from django.core.urlresolvers import reverse


def test_urls_materia():
    st = reverse('materia:pesquisar_materia_list')
    assert st == '/materia/pesquisar-materia-list'
