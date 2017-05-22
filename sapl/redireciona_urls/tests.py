from django.core.urlresolvers import reverse
from django.test import TestCase


class RedirecionaURLsTests(TestCase):
    def test_redireciona_index_SAPL(self):
        response = self.client.get(reverse(
            'sapl.redireciona_urls:redireciona_sapl_index')
        )
        url_e = reverse('sapl_index')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


class RedirecionaParlamentarTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_parlamentar'

    def test_redireciona_parlamentar_list(self):
        url = reverse(self.url_pattern)
        url_e = reverse('sapl.parlamentares:parlamentar_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_parlamentar_list_por_legislatura(self):
        numero_legislatura = 123

        url = reverse(self.url_pattern)
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
        url = reverse(self.url_pattern)
        pk_parlamentar = 21
        url = "%s%s" % (url, "?cod_parlamentar=%s" % (pk_parlamentar))
        url_e = reverse(
            'sapl.parlamentares:parlamentar_detail',
            kwargs = {'pk': pk_parlamentar}
            )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


class RedirecionaComissaoTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_comissao'

    def test_redireciona_comissao_detail(self):
        url = reverse(self.url_pattern)
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
        url = reverse(self.url_pattern)
        url_e = reverse(
            'sapl.comissoes:comissao_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


class RedirecionaPautaSessaoTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_pauta_sessao_'

    def test_redireciona_pauta_sessao_detail(self):
        url = reverse(self.url_pattern)
        pk_pauta_sessao = 21
        url = "%s%s" % (url, "?cod_sessao_plen=%s" % (pk_pauta_sessao))
        url_e = reverse(
            'sapl.sessao:pauta_sessao_detail',
            kwargs = {'pk': pk_pauta_sessao}
            )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_pauta_sessao_list(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_pauta')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_pauta_sessao_list_por_dat_sessao_sel(self):

        url = reverse(self.url_pattern)

        ano_s_p = "2016"
        mes_s_p = "05"
        dia_s_p = "14"
        data_s_p = "%s/%s/%s" % (dia_s_p, mes_s_p, ano_s_p)

        url = "%s%s" % (url, "?dat_sessao_sel=%s" % data_s_p)

        url_e = reverse( 'sapl.sessao:pesquisar_pauta')

        args_e = ''
        args_e += "?data_inicio__year=%s" % (ano_s_p)
        args_e += "&data_inicio__month=%s" % (mes_s_p.lstrip("0"))
        args_e += "&data_inicio__day=%s" % (dia_s_p.lstrip("0"))
        args_e += "&tipo=&salvar=Pesquisar"

        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


class RedirecionaMesaDiretoraTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_mesa_diretora'

    def test_redireciona_mesa_diretora(self):
        url = reverse(self.url_pattern)
        url_e = reverse('sapl.parlamentares:mesa_diretora')

        response = self.client.get(url)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


class RedirecionaMesaDiretoraParlamentarTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_mesa_diretora_parlamentar'

    def test_redireciona_mesa_diretora_parlamentar(self):
        url = reverse(self.url_pattern)
        pk_parlamentar = 21
        url = "%s%s" % (url, "?cod_parlamentar=%s" % (pk_parlamentar))
        url_e = reverse(
            'sapl.parlamentares:parlamentar_detail',
            kwargs = {'pk': pk_parlamentar}
            )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)


class RedirecionaSessaoPlenariaTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_sessao_plenaria_'

    def test_redireciona_sessao_plenaria_detail(self):
        url = reverse(self.url_pattern)
        pk_sessao_plenaria = 258
        url = "%s%s" % (url, "?cod_sessao_plen=%s" % (pk_sessao_plenaria))
        url_e = reverse(
            'sapl.sessao:sessaoplenaria_detail',
            kwargs = {'pk': pk_sessao_plenaria}
            )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_parametro(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = ''
        month = ''
        day = ''
        tipo_sessao = ''

        args = ''
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = ''
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_tipo(self):
        # import ipdb; ipdb.set_trace()
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = '2015'
        month = '04'
        day = '06'
        tipo_sessao = ''

        args = ''
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = ''
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_tipo_e_ano(self):
        # import ipdb; ipdb.set_trace()
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = ''
        month = '04'
        day = '06'
        tipo_sessao = ''

        args = ''
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = ''
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_ano(self):
        # import ipdb; ipdb.set_trace()
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = ''
        month = '04'
        day = '06'
        tipo_sessao = '4'

        args = ''
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = ''
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_mes_dia(self):
        # import ipdb; ipdb.set_trace()
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = '2015'
        month = ''
        day = ''
        tipo_sessao = '4'

        args = ''
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = ''
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, url_e)
