import pytest
from django_webtest import DjangoTestApp, WebTestMixin


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
