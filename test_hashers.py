from sapl.hashers import (ZopeSHA1PasswordHasher,
                          zope_encoded_password_to_django)


def test_zope_encoded_password_to_django():
    password = 'saploper'
    encoded = '{SSHA}Swzvwt/2lSJfA8KUOl6cRjkpmHLkLkmsKu28'
    salt = '5C5JrCrtvA=='
    migrated = zope_encoded_password_to_django(encoded)
    encoded = ZopeSHA1PasswordHasher().encode(password, salt)
    assert migrated == encoded
