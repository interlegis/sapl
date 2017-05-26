from django.core.urlresolvers import reverse
from django.test import TestCase

MovedPermanentlyHTTPStatusCode = 301
EMPTY_STRING = ''


class RedirecionaURLsTests(TestCase):
    def test_redireciona_index_SAPL(self):
        response = self.client.get(reverse(
            'sapl.redireciona_urls:redireciona_sapl_index')
        )
        url_e = reverse('sapl_index')
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)


class RedirecionaParlamentarTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_parlamentar'

    def test_redireciona_parlamentar_list(self):
        url = reverse(self.url_pattern)
        url_e = reverse('sapl.parlamentares:parlamentar_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
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

        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
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
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
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
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_comissao_list(self):
        url = reverse(self.url_pattern)
        url_e = reverse(
            'sapl.comissoes:comissao_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
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
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_pauta_sessao_list(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_pauta')

        response = self.client.get(url)

        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_pauta_sessao_list_por_dat_sessao_sel(self):

        url = reverse(self.url_pattern)

        ano_s_p = "2016"
        mes_s_p = "05"
        dia_s_p = "14"
        data_s_p = "%s/%s/%s" % (dia_s_p, mes_s_p, ano_s_p)

        url = "%s%s" % (url, "?dat_sessao_sel=%s" % data_s_p)

        url_e = reverse( 'sapl.sessao:pesquisar_pauta')

        args_e = EMPTY_STRING
        args_e += "?data_inicio__year=%s" % (ano_s_p)
        args_e += "&data_inicio__month=%s" % (mes_s_p.lstrip("0"))
        args_e += "&data_inicio__day=%s" % (dia_s_p.lstrip("0"))
        args_e += "&tipo=&salvar=Pesquisar"

        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)

        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)


class RedirecionaMesaDiretoraTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_mesa_diretora'

    def test_redireciona_mesa_diretora(self):
        url = reverse(self.url_pattern)
        url_e = reverse('sapl.parlamentares:mesa_diretora')

        response = self.client.get(url)

        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
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

        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)


class RedirecionaNormasJuridicasListTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_norma_juridica_pesquisa'

    def test_redireciona_norma_juridica_pesquisa_sem_parametros(self):
        url = reverse(self.url_pattern)
        url_e = reverse('sapl.norma:norma_pesquisa')

        tipo_norma = EMPTY_STRING
        numero_norma = EMPTY_STRING
        ano_norma = EMPTY_STRING
        periodo_inicial_aprovacao = EMPTY_STRING
        periodo_final_aprovacao = EMPTY_STRING
        periodo_inicial_publicacao = EMPTY_STRING
        periodo_final_publicacao = EMPTY_STRING
        ementa_norma = EMPTY_STRING
        assuntos_norma = EMPTY_STRING

        args = EMPTY_STRING
        args += "?lst_tip_norma=%s" % (tipo_norma)
        args += "&txt_numero=%s" % (numero_norma)
        args += "&txt_ano=%s" % (ano_norma)
        args += "&dt_norma=%s" % (periodo_inicial_aprovacao)
        args += "&dt_norma2=%s" % (periodo_final_aprovacao)
        args += "&dt_public=%s" % (periodo_inicial_publicacao)
        args += "&dt_public2=%s" % (periodo_final_publicacao)
        args += "&txt_assunto=%s" % (ementa_norma)
        args += "&lst_assunto_norma=%s" % (assuntos_norma)
        args += "&salvar=%s" % ('Pesquisar')
        url = "%s%s" % (url, args)

        args_e = EMPTY_STRING
        args_e += "?tipo=%s" % (tipo_norma)
        args_e += "&numero=%s" % (numero_norma)
        args_e += "&ano=%s" % (ano_norma)
        args_e += "&data_0=%s" % (periodo_inicial_aprovacao)
        args_e += "&data_1=%s" % (periodo_final_aprovacao)
        args_e += "&data_publicacao_0=%s" % (periodo_inicial_publicacao)
        args_e += "&data_publicacao_1=%s" % (periodo_final_publicacao)
        args_e += "&ementa=%s" % (ementa_norma)
        args_e += "&assuntos=%s" % (assuntos_norma)
        args_e += "&salvar=%s" % ('Pesquisar')
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_norma_juridica_pesquisa_por_tipo(self):
        url = reverse(self.url_pattern)
        url_e = reverse('sapl.norma:norma_pesquisa')

        tipo_norma = '4'
        numero_norma = EMPTY_STRING
        ano_norma = EMPTY_STRING
        periodo_inicial_aprovacao = EMPTY_STRING
        periodo_final_aprovacao = EMPTY_STRING
        periodo_inicial_publicacao = EMPTY_STRING
        periodo_final_publicacao = EMPTY_STRING
        ementa_norma = EMPTY_STRING
        assuntos_norma = EMPTY_STRING

        args = EMPTY_STRING
        args += "?lst_tip_norma=%s" % (tipo_norma)
        args += "&txt_numero=%s" % (numero_norma)
        args += "&txt_ano=%s" % (ano_norma)
        args += "&dt_norma=%s" % (periodo_inicial_aprovacao)
        args += "&dt_norma2=%s" % (periodo_final_aprovacao)
        args += "&dt_public=%s" % (periodo_inicial_publicacao)
        args += "&dt_public2=%s" % (periodo_final_publicacao)
        args += "&txt_assunto=%s" % (ementa_norma)
        args += "&lst_assunto_norma=%s" % (assuntos_norma)
        args += "&salvar=%s" % ('Pesquisar')
        url = "%s%s" % (url, args)

        args_e = EMPTY_STRING
        args_e += "?tipo=%s" % (tipo_norma)
        args_e += "&numero=%s" % (numero_norma)
        args_e += "&ano=%s" % (ano_norma)
        args_e += "&data_0=%s" % (periodo_inicial_aprovacao)
        args_e += "&data_1=%s" % (periodo_final_aprovacao)
        args_e += "&data_publicacao_0=%s" % (periodo_inicial_publicacao)
        args_e += "&data_publicacao_1=%s" % (periodo_final_publicacao)
        args_e += "&ementa=%s" % (ementa_norma)
        args_e += "&assuntos=%s" % (assuntos_norma)
        args_e += "&salvar=%s" % ('Pesquisar')
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_norma_juridica_pesquisa_por_ano(self):
        url = reverse(self.url_pattern)
        url_e = reverse('sapl.norma:norma_pesquisa')

        tipo_norma = EMPTY_STRING
        numero_norma = EMPTY_STRING
        ano_norma = '2010'
        periodo_inicial_aprovacao = EMPTY_STRING
        periodo_final_aprovacao = EMPTY_STRING
        periodo_inicial_publicacao = EMPTY_STRING
        periodo_final_publicacao = EMPTY_STRING
        ementa_norma = EMPTY_STRING
        assuntos_norma = EMPTY_STRING

        args = EMPTY_STRING
        args += "?lst_tip_norma=%s" % (tipo_norma)
        args += "&txt_numero=%s" % (numero_norma)
        args += "&txt_ano=%s" % (ano_norma)
        args += "&dt_norma=%s" % (periodo_inicial_aprovacao)
        args += "&dt_norma2=%s" % (periodo_final_aprovacao)
        args += "&dt_public=%s" % (periodo_inicial_publicacao)
        args += "&dt_public2=%s" % (periodo_final_publicacao)
        args += "&txt_assunto=%s" % (ementa_norma)
        args += "&lst_assunto_norma=%s" % (assuntos_norma)
        args += "&salvar=%s" % ('Pesquisar')
        url = "%s%s" % (url, args)

        args_e = EMPTY_STRING
        args_e += "?tipo=%s" % (tipo_norma)
        args_e += "&numero=%s" % (numero_norma)
        args_e += "&ano=%s" % (ano_norma)
        args_e += "&data_0=%s" % (periodo_inicial_aprovacao)
        args_e += "&data_1=%s" % (periodo_final_aprovacao)
        args_e += "&data_publicacao_0=%s" % (periodo_inicial_publicacao)
        args_e += "&data_publicacao_1=%s" % (periodo_final_publicacao)
        args_e += "&ementa=%s" % (ementa_norma)
        args_e += "&assuntos=%s" % (assuntos_norma)
        args_e += "&salvar=%s" % ('Pesquisar')
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)


class RedirecionaNormasJuridicasDetailTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_norma_juridica_detail'

    def test_redireciona_norma_juridica_detail(self):
        url = reverse(self.url_pattern)

        pk_norma = 120

        args = EMPTY_STRING
        args += "?cod_norma=%s" % (pk_norma)
        url = "%s%s" % (url, args)

        url_e = reverse(
            'sapl.norma:normajuridica_detail',
            kwargs={
                'pk': pk_norma}
            )
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_norma_juridica_detail_sem_parametros(self):
        url = reverse(self.url_pattern)

        pk_norma = EMPTY_STRING

        args = EMPTY_STRING
        args += "?cod_norma=%s" % (pk_norma)
        url = "%s%s" % (url, args)

        url_e = reverse('sapl.norma:norma_pesquisa')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
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

        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_parametro(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = EMPTY_STRING
        month = EMPTY_STRING
        day = EMPTY_STRING
        tipo_sessao = EMPTY_STRING

        args = EMPTY_STRING
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = EMPTY_STRING
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_tipo(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = '2015'
        month = '04'
        day = '06'
        tipo_sessao = EMPTY_STRING

        args = EMPTY_STRING
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = EMPTY_STRING
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_tipo_e_ano(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = EMPTY_STRING
        month = '04'
        day = '06'
        tipo_sessao = EMPTY_STRING

        args = EMPTY_STRING
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = EMPTY_STRING
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_ano(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = EMPTY_STRING
        month = '04'
        day = '06'
        tipo_sessao = '4'

        args = EMPTY_STRING
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = EMPTY_STRING
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)
        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_sessao_plenaria_list_sem_mes_dia(self):
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.sessao:pesquisar_sessao')

        year = '2015'
        month = EMPTY_STRING
        day = EMPTY_STRING
        tipo_sessao = '4'

        args = EMPTY_STRING
        args += "?ano_sessao_sel=%s" % (year)
        args += "&mes_sessao_sel=%s" % (month)
        args += "&dia_sessao_sel=%s" % (day)
        args += "&tip_sessao_sel=%s" % (tipo_sessao)
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        day = day.lstrip("0")
        month = month.lstrip("0")
        args_e = EMPTY_STRING
        args_e += "?data_inicio__year=%s" % (year)
        args_e += "&data_inicio__month=%s" % (month)
        args_e += "&data_inicio__day=%s" % (day)
        args_e += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
        url_e = "%s%s" % (url_e, args_e)
        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)


class RedirecionaHistoricoTramitacoesListTests(TestCase):
    url_pattern = 'sapl.redireciona_urls:redireciona_historico_tramitacoes'

    def test_redireciona_historico_tramitacoes_sem_parametros(self):
        args_e = EMPTY_STRING
        args = EMPTY_STRING
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.base:historico_tramitacoes')

        inicio_intervalo_data_tramitacao = EMPTY_STRING
        fim_intervalo_data_tramitacao = EMPTY_STRING
        tipo_materia = EMPTY_STRING
        unidade_local_tramitacao = EMPTY_STRING
        status_tramitacao = EMPTY_STRING

        args += "?txt_dat_inicio_periodo=%s" % (inicio_intervalo_data_tramitacao)
        args += "&txt_dat_fim_periodo=%s" % (fim_intervalo_data_tramitacao)
        args += "&lst_tip_materia=%s" % (tipo_materia)
        args += "&lst_cod_unid_tram_dest=%s" % (unidade_local_tramitacao)
        args += "&lst_status=%s" % (status_tramitacao)
        args += "&btn_materia_pesquisar=%s" % ('Pesquisar')
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        inicio_intervalo_data_tramitacao = inicio_intervalo_data_tramitacao.lstrip("0")
        fim_intervalo_data_tramitacao = fim_intervalo_data_tramitacao.lstrip("0")
        tipo_materia = tipo_materia.lstrip("0")
        unidade_local_tramitacao = unidade_local_tramitacao.lstrip("0")
        status_tramitacao = status_tramitacao.lstrip("0")

        if ((inicio_intervalo_data_tramitacao != EMPTY_STRING) or
            (fim_intervalo_data_tramitacao != EMPTY_STRING) or
            (tipo_materia != EMPTY_STRING) or
            (unidade_local_tramitacao != EMPTY_STRING) or
            (status_tramitacao != EMPTY_STRING)
            ):
            args_e += "?tramitacao__data_tramitacao_0=%s" % (
                    inicio_intervalo_data_tramitacao)
            args_e += "&tramitacao__data_tramitacao_1=%s" % (
                    fim_intervalo_data_tramitacao)
            args_e += "&tipo=%s" % (tipo_materia)
            args_e += "&tramitacao__unidade_tramitacao_local=%s" % (
                    unidade_local_tramitacao)
            args_e += "&tramitacao__status=%s" % (status_tramitacao)
            args_e += "&salvar=%s" % ('Pesquisar')

            url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)

    def test_redireciona_historico_tramitacoes(self):
        args = EMPTY_STRING
        args_e = EMPTY_STRING
        url = reverse(self.url_pattern)
        url_e = reverse( 'sapl.base:historico_tramitacoes')

        inicio_intervalo_data_tramitacao = '12/07/2000'
        fim_intervalo_data_tramitacao = '26/05/2017'
        unidade_local_tramitacao = '0'
        tipo_materia = '0'
        status_tramitacao = '0'

        args += "?txt_dat_inicio_periodo=%s" % (inicio_intervalo_data_tramitacao)
        args += "&txt_dat_fim_periodo=%s" % (fim_intervalo_data_tramitacao)
        args += "&lst_tip_materia=%s" % (tipo_materia)
        args += "&lst_cod_unid_tram_dest=%s" % (unidade_local_tramitacao)
        args += "&lst_status=%s" % (status_tramitacao)
        args += "&btn_materia_pesquisar=%s" % ('Pesquisar')
        url = "%s%s" % (url, args)

        # Remove zeros à esquerda
        inicio_intervalo_data_tramitacao = inicio_intervalo_data_tramitacao.lstrip("0")
        fim_intervalo_data_tramitacao = fim_intervalo_data_tramitacao.lstrip("0")
        tipo_materia = tipo_materia.lstrip("0")
        unidade_local_tramitacao = unidade_local_tramitacao.lstrip("0")
        status_tramitacao = status_tramitacao.lstrip("0")

        if ((inicio_intervalo_data_tramitacao != EMPTY_STRING) or
            (fim_intervalo_data_tramitacao != EMPTY_STRING) or
            (tipo_materia != EMPTY_STRING) or
            (unidade_local_tramitacao != EMPTY_STRING) or
            (status_tramitacao != EMPTY_STRING)
            ):
            args_e += "?tramitacao__data_tramitacao_0=%s" % (
                    inicio_intervalo_data_tramitacao)
            args_e += "&tramitacao__data_tramitacao_1=%s" % (
                    fim_intervalo_data_tramitacao)
            args_e += "&tipo=%s" % (tipo_materia)
            args_e += "&tramitacao__unidade_tramitacao_local=%s" % (
                    unidade_local_tramitacao)
            args_e += "&tramitacao__status=%s" % (status_tramitacao)
            args_e += "&salvar=%s" % ('Pesquisar')

            url_e = "%s%s" % (url_e, args_e)

        response = self.client.get(url)
        self.assertEqual(response.status_code, MovedPermanentlyHTTPStatusCode)
        self.assertEqual(response.url, url_e)
