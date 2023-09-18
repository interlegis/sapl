#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import logging
import re
import secrets
import subprocess
import sys
import zipfile
from base64 import b64encode, b64decode
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import requests
from kazoo.client import KazooClient

#
# Este módulo deve ser executado na raiz do projeto
#

logging.basicConfig()

SECURITY_FILE_TEMPLATE = """
   {
        "authentication":{
        "blockUnknown": true,
        "class":"solr.BasicAuthPlugin",
        "credentials":{"%s":"%s %s"},
        "forwardCredentials": false,
        "realm": "Solr Login"
        },
        "authorization":{
            "class":"solr.RuleBasedAuthorizationPlugin",
            "permissions":[{"name":"security-edit", "role":"admin"}],
            "user-role":{"%s":"admin"}
        }
    }
"""

URL_PATTERN = 'https?://(([a-zA-Z0-9]+):([a-zA-Z0-9]+)@)?([a-zA-Z0-9.-]+)(:[0-9]{4})?'


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


def create_security_file(username, password):
    print("Creating security.json file...")
    with open("security.json", "w") as f:
        cypher, salt = solr_hash_password(password)
        f.write(SECURITY_FILE_TEMPLATE % (username, cypher, salt, username))
    print("file created!")


def upload_security_file(zk_host):
    zk_port = 9983  # embedded ZK port
    print(f"Uploading security file to Solr, ZK server={zk_host}:{zk_port}...")
    try:
        with open('security.json', 'r') as f:
            data = f.read()
        zk = KazooClient(hosts=f"{zk_host}:{zk_port}")
        zk.start()
        print("Uploading security.json file...")
        if zk.exists('/security.json'):
            zk.set("/security.json", str.encode(data))
        else:
            zk.create("/security.json", str.encode(data))
        data, stat = zk.get('/security.json')
        print("file uploaded!")
        print(data.decode('utf-8'))
        zk.stop()
    except Exception as e:
        print(e)
        sys.exit(-1)


class SolrClient:
    LIST_CONFIGSETS = "{}/solr/admin/configs?action=LIST&omitHeader=true&wt=json"
    UPLOAD_CONFIGSET = "{}/solr/admin/configs?action=UPLOAD&name={}&wt=json"
    LIST_COLLECTIONS = "{}/solr/admin/collections?action=LIST&wt=json"
    STATUS_COLLECTION = "{}/solr/admin/collections?action=CLUSTERSTATUS" \
                        "&collection={}&wt=json"
    STATUS_CORE = "{}/admin/cores?action=STATUS&name={}"
    EXISTS_COLLECTION = "{}/solr/{}/admin/ping?wt=json"
    OPTIMIZE_COLLECTION = "{}/solr/{}/update?optimize=true&wt=json"
    CREATE_COLLECTION = "{}/solr/admin/collections?action=CREATE&name={}" \
                        "&collection.configName={}&numShards={}" \
                        "&replicationFactor={}&maxShardsPerNode={}&wt=json"
    DELETE_COLLECTION = "{}/solr/admin/collections?action=DELETE&name={}&wt=json"
    DELETE_DATA = "{}/solr/{}/update?commitWithin=1000&overwrite=true&wt=json"
    QUERY_DATA = "{}/solr/{}/select?q=*:*"

    CONFIGSET_NAME = "sapl_configset"

    CONFIGSET_PATH = "./solr/sapl_configset/conf"

    def __init__(self, url):
        self.url = url

    def get_num_docs(self, collection_name):
        final_url = self.QUERY_DATA.format(self.url, collection_name)
        res = requests.get(final_url)
        if res.ok:
            try:
                dic = res.json()
                return dic["response"]["numFound"]
            except Exception as e:
                print(F"Erro no get_num_docs. Erro: {e}")
                print(res.content)

        return 0

    def list_collections(self):
        req_url = self.LIST_COLLECTIONS.format(self.url)
        res = requests.get(req_url)
        try:
            dic = res.json()
            return dic['collections']
        except Exception as e:
            print(F"Erro no list_collections. Erro: {e}")
            print(res.content)
            return 0

    def exists_collection(self, collection_name):
        collections = self.list_collections()
        return True if collection_name in collections else False

    def zip_configset(self):
        try:
            base_path = Path(self.CONFIGSET_PATH).expanduser().resolve(strict=True)

            # zip files in memory
            _zipfile = BytesIO()
            with zipfile.ZipFile(_zipfile, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in base_path.rglob('*'):
                    zipf.write(file, file.relative_to(base_path))
            return _zipfile
        except Exception as e:
            print(e)
            raise e

    def maybe_upload_configset(self, force=False):
        req_url = self.LIST_CONFIGSETS.format(self.url)
        res = requests.get(req_url)
        try:
            dic = res.json()
            configsets = dic['configSets']
        except Exception as e:
            print(F"Erro ao configurar configsets. Erro: {e}")
            print(res.content)

        # UPLOAD configset
        if not self.CONFIGSET_NAME in configsets or force:

            # GENERATE in memory configset
            configset_zip = self.zip_configset()
            data = configset_zip.getvalue()
            configset_zip.close()

            files = {'file': ('saplconfigset.zip',
                              data,
                              'application/octet-stream',
                              {'Expires': '0'})}

            req_url = self.UPLOAD_CONFIGSET.format(self.url, self.CONFIGSET_NAME)

            resp = requests.post(req_url, files=files)
            print(resp.content)

        else:
            print('O %s já presente no servidor, NÃO enviando.' % self.CONFIGSET_NAME)

    def create_collection(self, collection_name, shards=1, replication_factor=1, max_shards_per_node=1):
        self.maybe_upload_configset()
        req_url = self.CREATE_COLLECTION.format(self.url,
                                                collection_name,
                                                self.CONFIGSET_NAME,
                                                shards,
                                                replication_factor,
                                                max_shards_per_node)
        res = requests.post(req_url)
        if res.ok:
            print("Collection '%s' created succesfully" % collection_name)
        else:
            print("Error creating collection '%s'" % collection_name)
            try:
                as_json = res.json()
                print("Error %s: %s" % (res.status_code, as_json['error']['msg']))
            except Exception as e:
                print(F"Erro ao verificar erro na resposta. Erro: {e}")
                print(res.content)
            return False
        return True

    def delete_collection(self, collection_name):
        if collection_name == '*':
            collections = self.list_collections()
        else:
            collections = [collection_name]

        for c in collections:
            req_url = self.DELETE_COLLECTION.format(self.url, c)
            res = requests.post(req_url)
            if not res.ok:
                print("Error deleting collection '%s'", c)
                print("Code {}: {}".format(res.status_code, res.text))
            else:
                print("Collection '%s' deleted successfully!" % c)

    def delete_index_data(self, collection_name):
        req_url = self.DELETE_DATA.format(self.url, collection_name)
        res = requests.post(req_url,
                            data='<delete><query>*:*</query></delete>',
                            headers={'Content-Type': 'application/xml'})
        if not res.ok:
            print("Error deleting index for collection '%s'", collection_name)
            print("Code {}: {}".format(res.status_code, res.text))
        else:
            print("Collection '%s' data deleted successfully!" % collection_name)

            num_docs = self.get_num_docs(collection_name)
            print("Num docs: %s" % num_docs)


def setup_embedded_zk(solr_url):
    match = re.match(URL_PATTERN, solr_url)
    if match:
        _, solr_user, solr_pwd, solr_host, solr_port = match.groups()

        if solr_user and solr_pwd and solr_host:
            create_security_file(solr_user, solr_pwd)
            upload_security_file(solr_host)
        else:
            print(f"Missing Solr's username, password, and host: {solr_user}/{solr_pwd}/{solr_host}")
            sys.exit(-1)
    else:
        print(f"Solr URL path doesn't match the required format: {solr_url}")
        sys.exit(-1)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Cria uma collection no Solr')

    # required arguments
    parser.add_argument('-u', type=str, metavar='URL', nargs=1, dest='url',
                        required=True, help='Endereço do servidor Solr na forma http(s)://<address>[:port]')
    parser.add_argument('-c', type=str, metavar='COLLECTION', dest='collection', nargs=1,
                        required=True, help='Collection Solr a ser criada')

    # optional arguments
    parser.add_argument('-s', type=int, dest='shards', nargs='?',
                        help='Number of shards (default=1)', default=1)
    parser.add_argument('-rf', type=int, dest='replication_factor', nargs='?',
                        help='Replication factor (default=1)', default=1)
    parser.add_argument('-ms', type=int, dest='max_shards_per_node', nargs='?',
                        help='Max shards per node (default=1)', default=1)

    parser.add_argument("--embedded_zk", default=False, action="store_true",
                        help="Embedded ZooKeeper")

    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))
        sys.exit(-1)

    url = args.url.pop()

    if args.embedded_zk:
        print("Setup embedded ZooKeeper...")
        setup_embedded_zk(url)

    collection = args.collection.pop()
    client = SolrClient(url=url)

    ## Add --force to force upload security.json, configset upload and collection recreation
    ## it will clean the solr server before proceeding
    ## Add --clean option to clean uploadconfig and collection
    if not client.exists_collection(collection):
        print("Collection '%s' doesn't exists. Creating a new one..." % collection)
        created = client.create_collection(collection,
                                           shards=args.shards,
                                           replication_factor=args.replication_factor,
                                           max_shards_per_node=args.max_shards_per_node)
        if not created:
            sys.exit(-1)
    else:
        print("Collection '%s' exists." % collection)

    ## Add --disable-index to disable auto index
    num_docs = client.get_num_docs(collection)
    if num_docs == 0:
        print("Performing a full reindex of '%s' collection..." % collection)
        p = subprocess.call(["python3", "manage.py", "rebuild_index", "--noinput"])
