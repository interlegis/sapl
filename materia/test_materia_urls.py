from django.core.urlresolvers import reverse


def test_urls_materia():
    st = reverse('materia:pesquisar_materia_list')
    assert st == '/materia/pesquisar-materia-list'

    st = reverse('materia:relatoria_edit', kwargs={'pk': '11', 'id': '99'})
    assert st == '/materia/11/relatoria/99/edit'

    st = reverse('materia:tramitacao_edit', kwargs={'pk': '3', 'id': '8'})
    assert st == '/materia/3/tramitacao/8/edit'

    st = reverse('materia:adicionar_proposicao')
    assert st == '/materia/proposicao'

    st = reverse('materia:editar_proposicao', kwargs={'pk': '3'})
    assert st == '/materia/proposicao/3/edit'

    st = reverse('materia:list_proposicao')
    assert st == '/materia/proposicao_list'
