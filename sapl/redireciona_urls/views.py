from .exceptions import UnknownUrlNameError

from django.core.urlresolvers import NoReverseMatch, reverse
from django.views.generic import RedirectView

from sapl.parlamentares.apps import AppConfig as parlamentaresConfig
from sapl.comissoes.apps import AppConfig as comissoesConfig
from sapl.materia.apps import AppConfig as materiaConfig
from sapl.sessao.apps import AppConfig as sessaoConfig
from sapl.base.apps import AppConfig as relatoriosConfig

app_parlamentares = parlamentaresConfig.name
app_comissoes = comissoesConfig.name
app_materia = materiaConfig.name
app_sessao = sessaoConfig.name
app_relatorios = relatoriosConfig.name

parlamentar_list = ( app_parlamentares + ':parlamentar_list')
parlamentar_detail = (app_parlamentares + ':parlamentar_detail')
parlamentar_mesa_diretora = (app_parlamentares + ':mesa_diretora')

comissao_list = (app_comissoes + ':comissao_list')
comissao_detail = (app_comissoes + ':comissao_detail')


materialegislativa_detail = (app_materia + ':materialegislativa_detail')
materialegislativa_list = (app_materia + ':pesquisar_materia')

pauta_sessao_list = (app_sessao + ':pesquisar_pauta')
pauta_sessao_detail = (app_sessao + ':pauta_sessao_detail')
sessao_plenaria_list = (app_sessao + ':pesquisar_sessao')
sessao_plenaria_detail = (app_sessao + ':sessaoplenaria_detail')

relatorios_list = (app_relatorios + ':relatorios_list')
relatorio_materia_por_tramitacao = (app_relatorios + ':materia_por_tramitacao')


class RedirecionaSAPLIndex(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url_pattern = 'sapl_index'
        try:
            url = reverse(url_pattern)
        except NoReverseMatch:
            raise UnknownUrlNameError(url_pattern)
        return url


class RedirecionaParlamentar(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = ''
        pk_parlamentar = self.request.GET.get('cod_parlamentar', '')

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

            numero_legislatura = self.request.GET.get('hdn_num_legislatura', '')
            if numero_legislatura:
                args = '?pk=' + numero_legislatura
                url = "%s%s" % (url, args)

        return url


class RedirecionaComissao(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = ''
        pk_comissao = self.request.GET.get('cod_comissao', '')

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
        return url


class RedirecionaPautaSessao(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk_sessao_plenaria = self.request.GET.get('cod_sessao_plen', '')

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


            data_sessao_plenaria = self.request.GET.get('dat_sessao_sel', '')

            if data_sessao_plenaria:
                dia_s_p, mes_s_p, ano_s_p = data_sessao_plenaria.split('/')
                # Remove zeros à esquerda de dia_s_p e mes_s_p
                dia_s_p = dia_s_p.lstrip("0")
                mes_s_p = mes_s_p.lstrip("0")
                args = ''
                args += "?data_inicio__year=%s" % (ano_s_p)
                args += "&data_inicio__month=%s" % (mes_s_p)
                args += "&data_inicio__day=%s" % (dia_s_p)
                args += "&tipo=&salvar=Pesquisar"
                url = "%s%s" % (url, args)

        return url


class RedirecionaSessaoPlenaria(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk_sessao_plenaria = self.request.GET.get('cod_sessao_plen', '')
        url = ''
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

            year = self.request.GET.get('ano_sessao_sel', '')
            month = self.request.GET.get('mes_sessao_sel', '')
            day = self.request.GET.get('dia_sessao_sel', '')
            tipo_sessao = self.request.GET.get('tip_sessao_sel', '')

            # Remove zeros à esquerda
            day = day.lstrip("0")
            month = month.lstrip("0")
            args = ''
            args += "?data_inicio__year=%s" % (year)
            args += "&data_inicio__month=%s" % (month)
            args += "&data_inicio__day=%s" % (day)
            args += "&tipo=%s&salvar=Pesquisar" % (tipo_sessao)
            url = "%s%s" % (url, args)

        return url


class RedirecionaRelatoriosList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = ''
        try:
            url = reverse(relatorios_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(relatorios_list)
        return url


class RedirecionaRelatoriosMateriasEmTramitacaoList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        url = ''
        try:
            url = reverse(relatorio_materia_por_tramitacao)
        except NoReverseMatch:
            raise UnknownUrlNameError(relatorio_materia_por_tramitacao)

        year = self.request.GET.get('selAno', '')
        if year:
            tramitacao_tipo = self.request.GET.get('lst_tip_materia', '')
            tramitacao_unidade_local = self.request.GET.get('lst_cod_unid_tram_dest', '')
            tramitacao_status = self.request.GET.get('lst_status', '')
            salvar = self.request.GET.get('btn_materia_pesquisar', 'Pesquisar')

            tramitacao_tipo = tramitacao_tipo.lstrip("0")
            tramitacao_unidade_local = tramitacao_unidade_local.lstrip("0")
            tramitacao_status = tramitacao_status.lstrip("0")

            args = ''
            args += "?ano=%s" % (year)
            args += "&tipo=%s" % (tramitacao_tipo)
            args += "&tramitacao__unidade_tramitacao_local=%s" % (tramitacao_unidade_local)
            args += "&tramitacao__status=%s" % (tramitacao_status)
            args += "&salvar=%s" % (salvar)
            url = "%s%s" % (url, args)

        return url


class RedirecionaMateriaLegislativaDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_materia', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(materialegislativa_detail, kwargs=kwargs)
        else:
            return reverse(materialegislativa_list)


class RedirecionaMateriaLegislativaList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        empty_string = ''
        url = empty_string
        args = empty_string
        try:
            url = reverse(materialegislativa_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(materialegislativa_list)

        tipo_materia = self.request.GET.get('lst_tip_materia', empty_string)
        numero_materia = self.request.GET.get('txt_numero', empty_string)
        ano_materia = self.request.GET.get('txt_ano', empty_string)
        numero_processo = self.request.GET.get('txt_npc', empty_string)
        num_protocolo_materia = self.request.GET.get('txt_num_protocolo', empty_string)
        periodo_inicial_apresentacao = self.request.GET.get('dt_apres', empty_string)
        periodo_final_apresentacao = self.request.GET.get('dt_apres2', empty_string)
        periodo_inicial_publicacao = self.request.GET.get('dt_public', empty_string)
        periodo_final_publicacao = self.request.GET.get('dt_public2', empty_string)
        hdn_cod_autor = self.request.GET.get('hdn_cod_autor', empty_string)
        tipo_autor = self.request.GET.get('lst_tip_autor', empty_string)
        ementa_materia = self.request.GET.get('txt_assunto', empty_string)
        tramitando = self.request.GET.get('rad_tramitando', empty_string)
        status_tramitacao = self.request.GET.get('lst_status', empty_string)

        args += "?tipo=%s" % (tipo_materia)
        args += "&numero=%s" % (numero_materia)
        args += "&ano=%s" % (ano_materia)
        args += "&numero_protocolo=%s" % (num_protocolo_materia)
        args += "&data_apresentacao_0=%s" % (periodo_inicial_apresentacao)
        args += "&data_apresentacao_1=%s" % (periodo_final_apresentacao)
        args += "&data_publicacao_0=%s" % (periodo_inicial_publicacao)
        args += "&data_publicacao_1=%s" % (periodo_final_publicacao)
        args += "&autoria__autor=%s" % (empty_string)
        args += "&autoria__autor__tipo=%s" % (tipo_autor)
        args += "&relatoria__parlamentar_id=%s" % (empty_string)
        args += "&local_origem_externa=%s" % (empty_string)
        args += "&tramitacao__unidade_tramitacao_destino=%s" % (empty_string)
        args += "&tramitacao__status=%s" % (status_tramitacao)
        args += "&em_tramitacao=%s" % (tramitando)
        args += "&o=%s" % (empty_string)
        args += "&materiaassunto__assunto=%s" % (empty_string)
        args += "&ementa=%s" % (ementa_materia)
        args += "&salvar=%s" % ('Pesquisar') # Default in both SAPL version

        url = "%s%s" % (url, args)

        return url


class RedirecionaMesaDiretoraView(RedirectView):
    permanent = True

    def get_redirect_url(self):
        try:
            url = reverse(parlamentar_mesa_diretora)
        except NoReverseMatch:
            raise UnknownUrlNameError(parlamentar_mesa_diretora)

        return url
