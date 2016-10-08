import os

if __name__ == '__main__':

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")
    django.setup()

if True:
    from sapl.urls import urlpatterns
    from django.core.urlresolvers import RegexURLResolver


class ListaUrls():

    def lista_urls(self, _urls):
        urls = []
        for item in _urls:
            if isinstance(item, RegexURLResolver) and \
                    item.app_name.startswith('sapl'):

                for key, value in item.reverse_dict.items():
                    if not isinstance(key, str):
                        if value:
                            url = value[0][0][0]
                            var = value[0][0][1]
                            urls.append((key, url, var, item.app_name))
        urls.sort(key=lambda x: x[1])
        return urls

    def __call__(self):
        return self.lista_urls(urlpatterns)


lista_urls = ListaUrls()
if __name__ == '__main__':
    _lista_urls = lista_urls()
    for url_item in _lista_urls:

        params = {}

        for v in url_item[2]:
            params[v] = 1

        u = '/' + url_item[1] % params
        print(url_item[3], u)
