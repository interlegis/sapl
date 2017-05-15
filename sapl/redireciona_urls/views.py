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

comissao_list = (app_comissoes + ':comissao_list')
comissao_detail = (app_comissoes + ':comissao_detail')


materialegislativa_detail = (app_materia + ':materialegislativa_detail')
materialegislativa_list = (app_materia + ':materialegislativa_list')

pauta_sessao_list = (app_sessao + ':pesquisar_pauta')
pauta_sessao_detail = (app_sessao + ':pauta_sessao_detail')
sessao_plenaria_list = (app_sessao + ':pesquisar_sessao')
sessao_plenaria_detail = (app_sessao + ':sessaoplenaria_detail')

relatorios_list = (app_relatorios + ':relatorios_list')
relatorio_materia_por_tramitacao = (app_relatorios + ':materia_por_tramitacao')


class RedirecionaSAPLIndex(RedirectView):
    permanent = True

    def get(self, request, *args, **kwargs):
        self.url = '/'
        return super(
            RedirecionaSAPLIndexRedirectView,
            self
            ).get(self, request, *args, **kwargs)

class RedirecionaParlamentarDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_parlamentar', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(parlamentar_detail, kwargs=kwargs)
        else:
            return reverse(parlamentar_list)


class RedirecionaParlamentarList(RedirectView):
    permanent = True
    query_string = True

    def get_redirect_url(self):
        try:
            url = reverse(parlamentar_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(parlamentar_list)

        pk = self.request.GET.get('hdn_num_legislatura', '')
        if pk:
            args = '?pk=' + pk
            url = "%s%s" % (url, args)

        return url


class RedirecionaComissaoList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        try:
            url = reverse(comissao_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(comissao_list)
        return url


class RedirecionaComissaoDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_comissao', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(comissao_detail, kwargs=kwargs)
        else:
            return reverse(comissao_list)


class RedirecionaPautaSessaoDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_sessao_plen', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(pauta_sessao_detail, kwargs=kwargs)
        else:
            return reverse(pauta_sessao_list)

class RedirecionaPautaSessaoList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        try:
            url = reverse(pauta_sessao_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(pauta_sessao_list)
        pk = self.request.GET.get('dat_sessao_sel', '')

        args = ''

        if pk:
            day, month, year = pk.split('/')
            # Remove zeros à esquerda
            day = day.lstrip("0")
            month = month.lstrip("0")
            args = "?data_inicio__year=%s" % (year)
            args += "&data_inicio__month=%s" % (month)
            args += "&data_inicio__day=%s" % (day)
            args += "&tipo=&salvar=Pesquisar" 
            url = "%s%s" % (url, args)

        return url


class RedirecionaSessaoPlenariaList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        try:
            url = reverse(sessao_plenaria_list)
        except NoReverseMatch:
            raise UnknownUrlNameError(sessao_plenaria_list)

        year = self.request.GET.get('ano_sessao_sel', '')
        if year:
            month = self.request.GET.get('mes_sessao_sel', '')
        else:
            month = ''

        if month:
            day = self.request.GET.get('dia_sessao_sel', '')
        else:
            day = ''

        tipo_sessao = self.request.GET.get('tip_sessao_sel', '')

        if tipo_sessao or year:
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


class RedirecionaSessaoPlenariaDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_sessao_plen', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(sessao_plenaria_detail, kwargs=kwargs)
        else:
            return reverse(sessao_plenaria_list)


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
