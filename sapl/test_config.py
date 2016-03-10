from .settings import EMAIL_PORT
from .settings import SECRET_KEY
from .settings import DEBUG
from .settings import DATABASES
from .settings import EMAIL_USE_TLS
from .settings import EMAIL_HOST
from .settings import EMAIL_HOST_USER
from .settings import EMAIL_HOST_PASSWORD

data = DATABASES.get('default')


def test_config():
    assert EMAIL_PORT == 587
    assert SECRET_KEY == '!9g1-#la+#(oft(v-y1qhy$jk-2$24pdk69#b_jfqyv!*%a_)t'
    assert DEBUG is True
    assert data.get('NAME') == 'sapl'
    assert data.get('USER') == 'sapl'
    assert data.get('PASSWORD') == 'sapl'
    assert data.get('HOST') == 'localhost'
    assert data.get('PORT') == '5432'
    assert EMAIL_USE_TLS is True
    assert EMAIL_HOST == 'smtp.interlegis.leg.br'
    assert EMAIL_HOST_USER == 'sapl-test'
    assert EMAIL_HOST_PASSWORD == '2BhCwbGHcZ'
