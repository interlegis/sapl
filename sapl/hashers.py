import base64
import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher, make_password
from django.utils.encoding import force_bytes


def to_base64(source):
    return base64.b64encode(source).decode('utf-8')


class ZopeSHA1PasswordHasher(PBKDF2PasswordHasher):
    """
    The SHA1 password hashing algorithm used by Zope.
    Zope uses `password + salt`, Django has `salt + password`.
    Pre encode with SHA1 in this order and PBKDF2 afterwards.

    based on https://www.fourdigits.nl/blog/converting-plone-data-to-django/
    """

    algorithm = "zope_sha1_pbkdf2"

    def encode(self, password, salt, iterations=None):
        assert password is not None
        assert salt
        password = force_bytes(password)
        decoded_salt = base64.b64decode(salt)

        # this is what is stored in zope
        hashed = hashlib.sha1(password + decoded_salt).digest() + decoded_salt
        hashed = to_base64(hashed)

        # encode again with the standard method
        return super().encode(hashed, salt, iterations)


def get_salt_from_zope_sha1(data):
    intermediate = base64.b64decode(data)
    salt = intermediate[20:].strip()
    return to_base64(salt)


ZOPE_SHA1_PREFIX = '{SSHA}'


def zope_encoded_password_to_django(encoded):
    "Migra um hash de senha do zope para uso com o ZopeSHA1PasswordHasher"

    if encoded.startswith(ZOPE_SHA1_PREFIX):
        data = encoded[len(ZOPE_SHA1_PREFIX):]
        salt = get_salt_from_zope_sha1(data)
        hasher = ZopeSHA1PasswordHasher()
        return super(ZopeSHA1PasswordHasher, hasher).encode(data, salt)
    else:
        # assume it's a plain password and use the default hashing
        return make_password(encoded)
