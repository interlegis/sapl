from django.core.urlresolvers import reverse


def test_reverse():
    assert '/comissoes/' == reverse('comissao:list')
    assert '/comissoes/create' == reverse('comissao:create')
    assert '/comissoes/2' == reverse('comissao:detail', args=(2,))
    assert '/comissoes/2/edit' == reverse('comissao:update', args=(2,))
    assert '/comissoes/2/delete' == reverse('comissao:delete', args=(2,))
