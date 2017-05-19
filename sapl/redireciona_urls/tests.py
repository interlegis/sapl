from django.core.urlresolvers import reverse
from django.test import TestCase

class RedirecionaURLsTests(TestCase):
    def test_redireciona_index_SAPL(self):
        # import ipdb; ipdb.set_trace()
        response = self.client.get(reverse(
            'sapl.redireciona_urls:redireciona_sapl_index')
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/")

    def test_redireciona_parlamentar_list(self):
        # import ipdb; ipdb.set_trace()
        url = reverse('sapl.redireciona_urls:redireciona_parlamentar')
        url_e = reverse('sapl.parlamentares:parlamentar_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_parlamentar_list_por_legislatura(self):
        numero_legislatura = 123

        url = reverse('sapl.redireciona_urls:redireciona_parlamentar')
        url_e = reverse('sapl.parlamentares:parlamentar_list')

        url = "%s%s" % (
            url,
            "?hdn_num_legislatura=%s" % (numero_legislatura)
            )
        url_e = "%s%s" % (url_e, "?pk=%s" % numero_legislatura)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_parlamentar_detail(self):
        url = reverse('sapl.redireciona_urls:redireciona_parlamentar')
        pk_parlamentar = 21
        url = "%s%s" % (url, "?cod_parlamentar=%s" % (pk_parlamentar))
        url_e = reverse(
            'sapl.parlamentares:parlamentar_detail',
            kwargs = {'pk': pk_parlamentar}
            )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


    def test_redireciona_comissao_detail(self):
        url = reverse('sapl.redireciona_urls:redireciona_comissao')
        pk_comissao = 21
        url = "%s%s" % (url, "?cod_comissao=%s" % (pk_comissao))
        url_e = reverse(
            'sapl.comissoes:comissao_detail',
            kwargs = {'pk': pk_comissao}
            )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


    def test_redireciona_comissao_list(self):
        url = reverse('sapl.redireciona_urls:redireciona_comissao')
        url_e = reverse(
            'sapl.comissoes:comissao_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)
