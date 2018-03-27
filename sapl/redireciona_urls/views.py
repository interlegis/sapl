from django.core.urlresolvers import NoReverseMatch, reverse
from django.views.generic import RedirectView

from sapl.base.apps import AppConfig as atasConfig
from sapl.comissoes.apps import AppConfig as comissoesConfig
from sapl.materia.apps import AppConfig as materiaConfig
from sapl.norma.apps import AppConfig as normaConfig
from sapl.parlamentares.apps import AppConfig as parlamentaresConfig
from sapl.sessao.apps import AppConfig as sessaoConfig
from sapl.audiencia.apps import AppConfig as audienciaConfig

from .exceptions import UnknownUrlNameError

EMPTY_STRING = ''

presenca_sessaoConfig = relatoriosConfig = atasConfig

app_parlamentares = parlamentaresConfig.name
app_atas = atasConfig.name
app_presenca_sessao = presenca_sessaoConfig.name
app_comissoes = comissoesConfig.name
app_materia = materiaConfig.name
app_sessao = sessaoConfig.name
app_norma = normaConfig.name
app_relatorios = relatoriosConfig.name
app_audiencia = audienciaConfig.name

pesquisar_atas = (app_atas + ':atas')
presenca_sessao = (app_presenca_sessao + ':presenca_sessao')
parlamentar_list = (app_parlamentares + ':parlamentar_list')
parlamentar_detail = (app_parlamentares + ':parlamentar_detail')
parlamentar_mesa_diretora = (app_parlamentares + ':mesa_diretora')

comissao_list = (app_comissoes + ':comissao_list')
comissao_detail = (app_comissoes + ':comissao_detail')

audiencia = (app_audiencia + ':audiencia')
reuniao_detail = (app_comissoes + ':reuniao_detail')

materialegislativa_detail = (app_materia + ':materialegislativa_detail')
materialegislativa_list = (app_materia + ':pesquisar_materia')

pauta_sessao_list = (app_sessao + ':pesquisar_pauta')
pauta_sessao_detail = (app_sessao + ':pauta_sessao_detail')
sessao_plenaria_list = (app_sessao + ':pesquisar_sessao')
sessao_plenaria_detail = (app_sessao + ':sessaoplenaria_detail')

norma_juridica_detail = (app_norma + ':normajuridica_detail')
norma_juridica_pesquisa = (app_norma + ':norma_pesquisa')

relatorios_list = (app_relatorios + ':relatorios_list')
relatorio_materia_por_tramitacao = (app_relatorios + ':materia_por_tramitacao')
relatorio_materia_por_autor = (app_relatorios + ':materia_por_autor')
relatorio_materia_por_ano_autor_tipo = (
    app_relatorios + ':materia_por_ano_autor_tipo')
historico_tramitacoes = (app_relatorios + ':historico_tramitacoes')


def has_iframe(url, request):

    iframe = request.GET.get(
        'iframe',
        EMPTY_STRING)
    if iframe:
        iframe_qs = ("iframe=" + iframe)
        url += ("&" if "?" in url else "?")
        url += iframe_qs

    return url


class RedirecionaSAPLIndex(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url_pattern = 'sapl_index'
        try:
            url = reverse(url_pattern)
        except NoReverseMatch:
            raise UnknownUrlNameError(url_pattern)

        url = has_iframe(url, self.request)

        return url


class RedirecionaParlamentar(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        pk_parlamentar = self.request.GET.get(
            'cod_parlamentar',
            EMPTY_STRING)

        if pk_parlamentar:
            try:
                kwargs = {'pk': pk_parlamentar}
                url = reverse(parlamentar_detail, kwargs=kwargs)
            except NoReverseMatch:
                raise UnknownUrlNameError(parlamentar_detail, kwargs=kwargs)
        else:
            try:
                url = reverse(parlamentar_list)
            except NoReverseMatch:
                raise UnknownUrlNameError(parlamentar_list)

            numero_legislatura = self.request.GET.get(
                'hdn_num_legislatura',
                EMPTY_STRING)
            if numero_legislatura:
                args = '?pk=' + numero_legislatura
                url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaComissao(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        pk_comissao = self.request.GET.get('cod_comissao', EMPTY_STRING)

        if pk_comissao:
            kwargs = {'pk': pk_comissao}

            try:
                url = reverse(comissao_detail, kwargs=kwargs)
            except NoReverseMatch:
                raise UnknownUrlNameError(comissao_detail)
        else:
            try:
                url = reverse(comissao_list)
            except NoReverseMatch:
                raise UnknownUrlNameError(comissao_list)

        url = has_iframe(url, self.request)

        return url


class RedirecionaPautaSessao(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk_sessao_plenaria = self.request.GET.get(
            'cod_sessao_plen',
            EMPTY_STRING)

        if pk_sessao_plenaria:
            kwargs = {'pk': pk_sessao_plenaria}
            try:
                url = reverse(pauta_sessao_detail, kwargs=kwargs)
            except NoReverseMatch:
                raise UnknownUrlNameError(pauta_sessao_detail)
        else:
            try:
                url = reverse(pauta_sessao_list)
            except NoReverseMatch:
                raise UnknownUrlNameError(pauta_sessao_list)

            data_sessao_plenaria = self.request.GET.get(
                'dat_sessao_sel',
                EMPTY_STRING)

            if data_sessao_plenaria:
                dia_s_p, mes_s_p, ano_s_p = data_sessao_plenaria.split('/')
                # Remove zeros à esquerda de dia_s_p e mes_s_p
                dia_s_p = dia_s_p.lstrip("0")
                mes_s_p = mes_s_p.lstrip("0")
                args = EMPTY_STRING
                args += "?data_inicio__year=%s" % (ano_s_p)
                args += "&data_inicio__month=%s" % (mes_s_p)
                args += "&data_inicio__day=%s" % (dia_s_p)
                args += "&tipo=&salvar=Pesquisar"
                url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaSessaoPlenaria(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk_sessao_plenaria = self.request.GET.get(
            'cod_sessao_plen',
            EMPTY_STRING)
        url = EMPTY_STRING
        if pk_sessao_plenaria:
            kwargs = {'pk': pk_sessao_plenaria}
            try:
                url = reverse(sessao_plenaria_detail, kwargs=kwargs)
            except NoReverseMatch:
                raise UnknownUrlNameError(sessao_plenaria_detail)

        else:
            try:
                url = reverse(sessao_plenaria_list)
            except NoReverseMatch:
                raise UnknownUrlNameError(sessao_plenaria_list)

            year = self.request.GET.get(
                'ano_sessao_sel',
                EMPTY_STRING)
            month = self.request.GET.get(
                'mes_sessao_sel',
                EMPTY_STRING)
            day = self.request.GET.get(
                'dia_sessao_sel',
                EMPTY_STRING)
            tipo_sessao = self.request.GET.get(
                'tip_sessao_sel',
                EMPTY_STRING)

            # Remove zeros à esquerda
            day = day.lstrip("0")
            month = month.lstrip("0")
            args = EMPTY_STRING
            args += "?data_inicio__year=%s" % (year)
            args += "&data_inicio__month=%s" % (month)
            args += "&data_inicio__day=%s" % (day)
            args += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
            url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaRelatoriosList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        try:
            url = reverse(relatorios_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(relatorios_list)

        url = has_iframe(url, self.request)

        return url


class RedirecionaRelatoriosMateriasEmTramitacaoList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        try:
            url = reverse(relatorio_materia_por_tramitacao)
        except NoReverseMatch:
            raise UnknownUrlNameError(relatorio_materia_por_tramitacao)

        year = self.request.GET.get(
            'selAno',
            EMPTY_STRING)
        if year:
            tramitacao_tipo = self.request.GET.get(
                'lst_tip_materia',
                EMPTY_STRING)
            tramitacao_unidade_local = self.request.GET.get(
                'lst_cod_unid_tram_dest',
                EMPTY_STRING)
            tramitacao_status = self.request.GET.get(
                'lst_status',
                EMPTY_STRING)
            salvar = self.request.GET.get(
                'btn_materia_pesquisar',
                'Pesquisar')

            tramitacao_tipo = tramitacao_tipo.lstrip("0")
            tramitacao_unidade_local = tramitacao_unidade_local.lstrip("0")
            tramitacao_status = tramitacao_status.lstrip("0")

            args = EMPTY_STRING
            args += "?ano=%s" % (year)
            args += "&tipo=%s" % (tramitacao_tipo)
            args += "&tramitacao__unidade_tramitacao_local=%s" % (
                tramitacao_unidade_local)
            args += "&tramitacao__status=%s" % (tramitacao_status)
            args += "&salvar=%s" % (salvar)
            url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaMateriaLegislativaDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        pk = self.request.GET.get('cod_materia', EMPTY_STRING)

        if pk:
            kwargs = {'pk': pk}
            url = reverse(materialegislativa_detail, kwargs=kwargs)
        else:
            url = reverse(materialegislativa_list)

        url = has_iframe(url, self.request)

        return url


class RedirecionaMateriaLegislativaList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        args = EMPTY_STRING
        try:
            url = reverse(materialegislativa_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(materialegislativa_list)

        tipo_materia = self.request.GET.get(
            'lst_tip_materia',
            EMPTY_STRING)
        numero_materia = self.request.GET.get(
            'txt_numero',
            EMPTY_STRING)
        ano_materia = self.request.GET.get(
            'txt_ano',
            EMPTY_STRING)
        num_protocolo_materia = self.request.GET.get(
            'txt_num_protocolo',
            EMPTY_STRING)
        periodo_inicial_apresentacao = self.request.GET.get(
            'dt_apres',
            EMPTY_STRING)
        periodo_final_apresentacao = self.request.GET.get(
            'dt_apres2',
            EMPTY_STRING)
        periodo_inicial_publicacao = self.request.GET.get(
            'dt_public',
            EMPTY_STRING)
        periodo_final_publicacao = self.request.GET.get(
            'dt_public2',
            EMPTY_STRING)
        tipo_autor = self.request.GET.get(
            'lst_tip_autor',
            EMPTY_STRING)
        ementa_materia = self.request.GET.get(
            'txt_assunto',
            EMPTY_STRING)
        tramitando = self.request.GET.get(
            'rad_tramitando',
            EMPTY_STRING)
        status_tramitacao = self.request.GET.get(
            'lst_status',
            EMPTY_STRING)

        args += "?tipo=%s" % (tipo_materia)
        args += "&numero=%s" % (numero_materia)
        args += "&ano=%s" % (ano_materia)
        args += "&numero_protocolo=%s" % (num_protocolo_materia)
        args += "&data_apresentacao_0=%s" % (periodo_inicial_apresentacao)
        args += "&data_apresentacao_1=%s" % (periodo_final_apresentacao)
        args += "&data_publicacao_0=%s" % (periodo_inicial_publicacao)
        args += "&data_publicacao_1=%s" % (periodo_final_publicacao)
        args += "&autoria__autor=%s" % (EMPTY_STRING)
        args += "&autoria__autor__tipo=%s" % (tipo_autor)
        args += "&relatoria__parlamentar_id=%s" % (EMPTY_STRING)
        args += "&local_origem_externa=%s" % (EMPTY_STRING)
        args += "&tramitacao__unidade_tramitacao_destino=%s" % (EMPTY_STRING)
        args += "&tramitacao__status=%s" % (status_tramitacao)
        args += "&em_tramitacao=%s" % (tramitando)
        args += "&o=%s" % (EMPTY_STRING)
        args += "&materiaassunto__assunto=%s" % (EMPTY_STRING)
        args += "&ementa=%s" % (ementa_materia)
        args += "&salvar=%s" % ('Pesquisar')  # Default in both SAPL version

        url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaMesaDiretoraView(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        try:
            url = reverse(parlamentar_mesa_diretora)
        except NoReverseMatch:
            raise UnknownUrlNameError(parlamentar_mesa_diretora)

        url = has_iframe(url, self.request)

        return url


class RedirecionaNormasJuridicasDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        pk_norma = self.request.GET.get('cod_norma', EMPTY_STRING)

        if pk_norma:
            kwargs = {'pk': pk_norma}
            url = reverse(norma_juridica_detail, kwargs=kwargs)
        else:
            url = reverse(norma_juridica_pesquisa)

        url = has_iframe(url, self.request)

        return url


class RedirecionaNormasJuridicasList(RedirectView):

    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        args = EMPTY_STRING
        try:
            url = reverse(norma_juridica_pesquisa)
        except NoReverseMatch:
            raise UnknownUrlNameError(norma_juridica_pesquisa)

        tipo_norma = self.request.GET.get(
            'lst_tip_norma',
            EMPTY_STRING)
        numero_norma = self.request.GET.get(
            'txt_numero',
            EMPTY_STRING)
        ano_norma = self.request.GET.get(
            'txt_ano',
            EMPTY_STRING)
        periodo_inicial_aprovacao = self.request.GET.get(
            'dt_norma',
            EMPTY_STRING)
        periodo_final_aprovacao = self.request.GET.get(
            'dt_norma2',
            EMPTY_STRING)
        periodo_inicial_publicacao = self.request.GET.get(
            'dt_public',
            EMPTY_STRING)
        periodo_final_publicacao = self.request.GET.get(
            'dt_public2',
            EMPTY_STRING)
        ementa_norma = self.request.GET.get(
            'txt_assunto',
            EMPTY_STRING)
        assuntos_norma = self.request.GET.get(
            'lst_assunto_norma',
            EMPTY_STRING)

        args += "?tipo=%s" % (tipo_norma)
        args += "&numero=%s" % (numero_norma)
        args += "&ano=%s" % (ano_norma)
        args += "&data_0=%s" % (periodo_inicial_aprovacao)
        args += "&data_1=%s" % (periodo_final_aprovacao)
        args += "&data_publicacao_0=%s" % (periodo_inicial_publicacao)
        args += "&data_publicacao_1=%s" % (periodo_final_publicacao)
        args += "&ementa=%s" % (ementa_norma)
        args += "&assuntos=%s" % (assuntos_norma)
        args += "&salvar=%s" % ('Pesquisar')  # Default in both SAPL version

        url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaHistoricoTramitacoesList(RedirectView):

    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        args = EMPTY_STRING
        try:
            url = reverse(historico_tramitacoes)
        except NoReverseMatch:
            raise UnknownUrlNameError(historico_tramitacoes)

        inicio_intervalo_data_tramitacao = self.request.GET.get(
            'txt_dat_inicio_periodo',
            EMPTY_STRING
        ).lstrip("0")
        fim_intervalo_data_tramitacao = self.request.GET.get(
            'txt_dat_fim_periodo',
            EMPTY_STRING
        ).lstrip("0")
        tipo_materia = self.request.GET.get(
            'lst_tip_materia',
            EMPTY_STRING
        ).lstrip("0")
        unidade_local_tramitacao = self.request.GET.get(
            'lst_cod_unid_tram_dest',
            EMPTY_STRING
        ).lstrip("0")
        status_tramitacao = self.request.GET.get(
            'lst_status',
            EMPTY_STRING
        ).lstrip("0")

        if (
            (inicio_intervalo_data_tramitacao != EMPTY_STRING) or
            (fim_intervalo_data_tramitacao != EMPTY_STRING) or
            (tipo_materia != EMPTY_STRING) or
            (unidade_local_tramitacao != EMPTY_STRING) or
                (status_tramitacao != EMPTY_STRING)):

            args += "?tramitacao__data_tramitacao_0=%s" % (
                inicio_intervalo_data_tramitacao)
            args += "&tramitacao__data_tramitacao_1=%s" % (
                fim_intervalo_data_tramitacao)
            args += "&tipo=%s" % (tipo_materia)
            args += "&tramitacao__unidade_tramitacao_local=%s" % (
                unidade_local_tramitacao)
            args += "&tramitacao__status=%s" % (status_tramitacao)
            args += "&salvar=%s" % ('Pesquisar')

            url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaAtasList(RedirectView):

    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        args = EMPTY_STRING
        try:
            url = reverse(pesquisar_atas)
        except NoReverseMatch:
            raise UnknownUrlNameError(pesquisar_atas)

        inicio_intervalo_data_ata = self.request.GET.get(
            'txt_dat_inicio',
            EMPTY_STRING
        ).lstrip("0")
        fim_intervalo_data_ata = self.request.GET.get(
            'txt_dat_fim',
            EMPTY_STRING
        ).lstrip("0")

        args += "?data_inicio_0=%s" % (
            inicio_intervalo_data_ata)
        args += "&data_inicio_1=%s" % (
            fim_intervalo_data_ata)
        args += "&salvar=%s" % ('Pesquisar')

        url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaPresencaParlamentares(RedirectView):

    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        args = EMPTY_STRING
        try:
            url = reverse(presenca_sessao)
        except NoReverseMatch:
            raise UnknownUrlNameError(presenca_sessao)

        inicio_intervalo_data_presenca_parlamentar = self.request.GET.get(
            'txt_dat_inicio',
            EMPTY_STRING
        ).lstrip("0")
        fim_intervalo_data_presenca_parlamentar = self.request.GET.get(
            'txt_dat_fim',
            EMPTY_STRING
        ).lstrip("0")

        args += "?data_inicio_0=%s" % (
            inicio_intervalo_data_presenca_parlamentar)
        args += "&data_inicio_1=%s" % (
            fim_intervalo_data_presenca_parlamentar)
        args += "&salvar=%s" % ('Pesquisar')

        url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaMateriasPorAutor(RedirectView):

    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        try:
            url = reverse(relatorio_materia_por_autor)
        except NoReverseMatch:
            raise UnknownUrlNameError(relatorio_materia_por_autor)

        url = has_iframe(url, self.request)

        return url


class RedirecionaMateriasPorAnoAutorTipo(RedirectView):

    permanent = True

    def get_redirect_url(self):
        url = EMPTY_STRING
        ano = self.request.GET.get('ano', '')

        try:
            url = reverse(relatorio_materia_por_ano_autor_tipo)
        except NoReverseMatch:
            raise UnknownUrlNameError(relatorio_materia_por_ano_autor_tipo)

        if ano:
            args = "?ano=%s" % (ano)
            args += "&salvar=%s" % ('Pesquisar')
            url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url


class RedirecionaReuniao(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk_reuniao = self.request.GET.get(
            'cod_comissao',
            EMPTY_STRING)
        url = EMPTY_STRING
        if pk_reuniao:
            kwargs = {'pk': pk_reuniao}
            try:
                url = reverse(reuniao_detail, kwargs=kwargs)
            except NoReverseMatch:
                raise UnknownUrlNameError(reuniao_detail)

        else:
            try:
                url = reverse(reuniao_list)
            except NoReverseMatch:
                raise UnknownUrlNameError(reuniao_list)

            year = self.request.GET.get(
                'ano_reuniao',
                EMPTY_STRING)
            month = self.request.GET.get(
                'mes_reuniao',
                EMPTY_STRING)
            day = self.request.GET.get(
                'dia_reuniao',
                EMPTY_STRING)
            tipo_reuniao = self.request.GET.get(
                'tip_reuniao',
                EMPTY_STRING)

            # Remove zeros à esquerda
            day = day.lstrip("0")
            month = month.lstrip("0")
            args = EMPTY_STRING
            args += "?data_inicio__year=%s" % (year)
            args += "&data_inicio__month=%s" % (month)
            args += "&data_inicio__day=%s" % (day)
            args += "&tipo=%s&salvar=Pesquisar" % (tipo_reuniao)
            url = "%s%s" % (url, args)

        url = has_iframe(url, self.request)

        return url
