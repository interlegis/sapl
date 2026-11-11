import pytest
from django_webtest import DjangoTestApp, WebTestMixin
from rest_framework.throttling import AnonRateThrottle


@pytest.fixture(autouse=True)
def sem_limite_de_requisicoes_da_api(monkeypatch):
    """
    Nos testes, todas as requisições anônimas vêm do mesmo endereço e o
    histórico do limite fica no cache entre um teste e outro. Os testes do
    limite (sapl/api/tests/test_api_abuso.py) definem a própria taxa.
    """
    monkeypatch.setattr(AnonRateThrottle, 'THROTTLE_RATES', {'anon': None})


class OurTestApp(DjangoTestApp):

    def __init__(self, *args, **kwargs):
        self.default_user = kwargs.pop('default_user', None)
        super(OurTestApp, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        kwargs.setdefault('user', self.default_user)
        kwargs.setdefault('auto_follow', True)
        return super(OurTestApp, self).get(*args, **kwargs)


@pytest.fixture(scope='function')
def app(request, admin_user):
    """WebTest's TestApp.

    Patch and unpatch settings before and after each test.

    WebTestMixin, when used in a unittest.TestCase, automatically calls
    _patch_settings() and _unpatchsettings.

    source: https://gist.github.com/magopian/6673250
    """
    wtm = WebTestMixin()
    wtm._patch_settings()
    request.addfinalizer(wtm._unpatch_settings)
    # XXX change this admin user to "saploper"
    return OurTestApp(default_user=admin_user.username)
