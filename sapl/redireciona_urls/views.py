from django.core.urlresolvers import NoReverseMatch, reverse
from django.views.generic import RedirectView


class RedirecionaParlamentarDetailRedirectView(RedirectView):
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


class RedirecionaParlamentarListRedirectView(RedirectView):
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
