from .settings import EMAIL_PORT


def test_config():
    assert EMAIL_PORT == 587
