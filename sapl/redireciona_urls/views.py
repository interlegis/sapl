from django.core.urlresolvers import NoReverseMatch, reverse
from django.views.generic import RedirectView


class RedirecionaSAPLIndex(RedirectView):
    permanent = True

    def get(self, request, *args, **kwargs):
        self.url = '/'
        return super(RedirecionaSAPLIndexRedirectView, self).get(self, request, *args, **kwargs)

class RedirecionaParlamentarDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_parlamentar', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(
                'sapl.parlamentares:parlamentar_detail',
                kwargs=kwargs)
        else:
            return reverse('sapl.parlamentares:parlamentar_list')


class RedirecionaParlamentarList(RedirectView):
    permanent = True
    query_string = True

    def get_redirect_url(self):

        try:
            url = reverse('sapl.parlamentares:parlamentar_list')
        except NoReverseMatch:
            return None
        pk = self.request.GET.get('hdn_num_legislatura', '')
        if pk:
            args = '?pk=' + pk
            url = "%s%s" % (url, args)

        return url


class RedirecionaComissaoList(RedirectView):
    permanent = True

    def get_redirect_url(self):

        try:
            url = reverse('sapl.comissoes:comissao_list')
        except NoReverseMatch:
            return None
        return url


class RedirecionaComissaoDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_comissao', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(
                'sapl.comissoes:comissao_detail',
                kwargs=kwargs)
        else:
            return reverse('sapl.comissoes:comissao_list')


class RedirecionaPautaSessaoDetail(RedirectView):
    permanent = True

    def get_redirect_url(self):
        pk = self.request.GET.get('cod_sessao_plen', '')

        if pk:
            kwargs = {'pk': pk}
            return reverse(
                'sapl.sessao:pauta_sessao_detail',
                kwargs=kwargs)
        else:
            return reverse('sapl.sessao:pesquisar_pauta')


class RedirecionaPautaSessaoList(RedirectView):
    permanent = True

    def get_redirect_url(self):
        try:
            url = reverse('sapl.sessao:pesquisar_pauta')
        except NoReverseMatch:
            return None

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
            url = reverse('sapl.sessao:pesquisar_sessao')
        except NoReverseMatch:
            return None

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
            return reverse(
                'sapl.sessao:sessaoplenaria_detail',
                kwargs=kwargs)
        else:
            return reverse('sapl.sessao:pesquisar_sessao')
