from django.contrib.sites.models import Site

from sapl import settings


class SiteMiddleware(object):
    def process_request(self, request):
        try:
            current_site = Site.objects.get(domain=request.get_host())
        except Site.DoesNotExist:
            current_site = Site.objects.get(id=1)

        request.current_site = current_site
        settings.HOST = request.get_host()

        import pdb; pdb.set_trace()
