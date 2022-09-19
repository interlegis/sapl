#!/usr/bin/env python
# -*- coding: utf-8 -*-

import secrets
import sys
from hashlib import sha256
from base64 import b64encode, b64decode

##
## Based on the logic here:
## https://www.planetcobalt.net/sdb/solr_password_hash.shtml
## http://www.mtitek.com/tutorials/solr/securing-solr-basic-auth.php
## https://github.com/apache/lucene-solr/blob/master/solr/core/src/java/org/apache/solr/security/Sha256AuthenticationProvider.java
##
## Usage:
## python solr_passwod.py <password> or python solr_password.py <password> <base_64_salt>
## or yet: cat password.txt | xargs python solr_password.py
##


def solr_hash_password(password: str, salt: str = None):
    """
        Generates a password and salt to be used in Basic Auth Solr

        password: clean text password string
        salt (optional): base64 salt string
        returns: sha256 hash of password and salt (both base64 strings)
    """
    m = sha256()
    if salt is None:
        salt = secrets.token_bytes(32)
    else:
        salt = b64decode(salt)
    m.update(salt + password.encode('utf-8'))
    digest = m.digest()

    m = sha256()
    m.update(digest)
    digest = m.digest()

    cypher = b64encode(digest).decode('utf-8')
    salt = b64encode(salt).decode('utf-8')
    return cypher, salt


def check_solr_hash(password: str, cypher: str, salt: str) -> bool:
    m = sha256()
    m.update(b64decode(salt) + password.encode('utf-8'))
    digest = m.digest()

    m = sha256()
    m.update(digest)
    digest = m.digest()

    return b64encode(digest).decode('utf-8') == cypher


def test_hash_password():
    password = "SolrRocks"
    salt = "Ndd7LKvVBAaZIF0QAVi1ekCfAJXr1GGfLtRUXhgrF8c="
    cypher = "IV0EHq1OnNrj6gvRCwvFwTrZ1+z1oBbnQdiVC3otuq0="
    ret = solr_hash_password(password, salt)
    assert ret[0] == cypher, "sha256 hashing of password failed!"

    cypher, salt = solr_hash_password(password)
    assert solr_hash_password(password, salt) == (cypher, salt)


def test_hash_check():
    password = "SolrRocks"
    salt = "Ndd7LKvVBAaZIF0QAVi1ekCfAJXr1GGfLtRUXhgrF8c="
    cypher = "IV0EHq1OnNrj6gvRCwvFwTrZ1+z1oBbnQdiVC3otuq0="

    assert check_solr_hash(password, cypher, salt), "Sha256 password check failed!"


if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: %s <password> [salt_base64]' % sys.argv[0])
        sys.exit(0)

    if len(sys.argv) == 3:
        _salt = sys.argv[2]
    else:
        _salt = None
    print("%s %s" % solr_hash_password(sys.argv[1], _salt))
