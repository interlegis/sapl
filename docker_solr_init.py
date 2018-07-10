
import requests
import subprocess
import sys


class SolrClient:

    LIST_CONFIGSETS = "{}://{}:{}/solr/admin/configs?action=LIST&omitHeader=true&wt=json"
    UPLOAD_CONFIGSET = "{}://{}:{}/solr/admin/configs?action=UPLOAD&name={}&wt=json"
    LIST_COLLECTIONS = "{}://{}:{}/solr/admin/collections?action=LIST&wt=json"
    STATUS_COLLECTION = "{}://{}:{}/solr/admin/collections?action=CLUSTERSTATUS&collection={}&wt=json"
    STATUS_CORE = "{}/admin/cores?action=STATUS&name={}"
    EXISTS_COLLECTION = "{}://{}:{}/solr/{}/admin/ping?wt=json"
    OPTIMIZE_COLLECTION = "{}://{}:{}/solr/{}/update?optimize=true&wt=json"
    CREATE_COLLECTION = "{}://{}:{}/solr/admin/collections?action=CREATE" \
                        "&name={}&collection.configName={}&numShards={}&replicationFactor={}&wt=json"
    DELETE_COLLECTION = "{}://{}:{}/solr/admin/collections?action=DELETE&name={}&wt=json"
    DELETE_DATA = "{}://{}:{}/solr/{}/update?commitWithin=1000&overwrite=true&wt=json"

    CONFIGSET_NAME = "sapl_configset"
    NUM_SHARDS = 1
    NUM_REPLICAS = 1

    def __init__(self, address='localhost', port=8983, protocol='http'):
        self.protocol = protocol
        self.address = address
        self.port = port

    def status_collection(self, collection_name):

        col_url = self.STATUS_COLLECTION.format(self.protocol, self.address, self.port, collection_name)
        resp = requests.get(col_url)
        status_cluster = resp.json()
        # TODO: test if collection exists!
        shards = status_cluster['cluster']['collections'][collection_name]['shards']
        num_docs = 0
        deleted_docs = 0
        for shard in shards.values():
            for replica in shard['replicas'].values():
                replica_base_url = replica['base_url']
                replica_core = replica['core']
                req_url = self.STATUS_CORE.format(replica_base_url, replica_core)
                resp = requests.get(req_url)
                data = resp.json()
                # TODO: test if collection exists!
                prefix = data['status'][replica_core]['index']
                num_docs += prefix['numDocs']
                deleted_docs += prefix['deletedDocs']
                # get a single replica per shard
                break
        return num_docs, deleted_docs

    def list_collections(self):
        req_url = self.LIST_COLLECTIONS.format(self.protocol, self.address, self.port)
        res = requests.get(req_url)
        dic = res.json()
        return dic['collections']

    def exists_collection(self, collection_name):
        collections = self.list_collections()
        return True if collection_name in collections else False

    def maybe_upload_configset(self, force=False):
        req_url = self.LIST_CONFIGSETS.format(self.protocol,
                                              self.address,
                                              self.port)
        res = requests.get(req_url)
        dic = res.json()
        configsets = dic['configSets']
        # UPLOAD configset
        if not self.CONFIGSET_NAME in configsets or force:
            files = {'file': ('saplconfigset.zip',
                              open('./solr/sapl_configset/conf/saplconfigset.zip',
                                   'rb'),
                              'application/octet-stream',
                              {'Expires': '0'})}

            req_url = self.UPLOAD_CONFIGSET.format(self.protocol, self.address, self.port, self.CONFIGSET_NAME)

            resp = requests.post(req_url, files=files)
            print(resp.content)
        else:
            print('O %s já presente no servidor, NÃO enviando.' % self.CONFIGSET_NAME)

    def create_collection(self, collection_name):
        self.maybe_upload_configset()
        req_url = self.CREATE_COLLECTION.format(self.protocol,
                                            self.address,
                                            self.port,
                                            collection_name,
                                            self.CONFIGSET_NAME,
                                            self.NUM_SHARDS,
                                            self.NUM_REPLICAS)
        print(req_url)
        res = requests.post(req_url)
        if res.ok:
            print("Collection '%s' created succesfully" % collection_name)
        else:
            print("Error creating collection '%s'" % collection_name)
            as_json = res.json()
            print("Error %s: %s" % (res.status_code, as_json['error']['msg']))
            return False
        return True

    # TODO: redo to collections
    # def optimize_collection(self, collection_name):
    #     req_url = self.OPTIMIZE_COLLECTION.format(self.protocol, self.address, self.port, collection_name)
    #     res = requests.get(req_url)
    #     if not res.ok:
    #         print("Error optimizing collection '{}'".format(collection_name))
    #         print("Code {}: {}".format(res.status_code, res.text))
    #     else:
    #         print("Collection '{}' optimized successfully!".format(collection_name))
    
    def delete_collection(self, collection_name):
        req_url = self.DELETE_COLLECTION.format(self.protocol, self.address, self.port, collection_name)
        res = requests.post(req_url)
        if not res.ok:
            print("Error deleting collection '%s'", collection_name)
            print("Code {}: {}".format(res.status_code, res.text))
        else:
            print("Collection '%s' deleted successfully!" % collection_name)

    def delete_index_data(self, collection_name):
        req_url = self.DELETE_DATA.format(self.protocol, self.address, self.port, collection_name)
        res = requests.post(req_url,
                            data='<delete><query>*:*</query></delete>',
                            headers={'Content-Type': 'application/xml'})
        if not res.ok:
            print("Error deleting index for collection '%s'", collection_name)
            print("Code {}: {}".format(res.status_code, res.text))
        else:
            print("Collection '%s' data deleted successfully!" % collection_name)

            indexed, deleted = self.status_collection(collection_name)
            print("Num docs: %s" % indexed)
            print("Delete docs: %s" % deleted)


if __name__ == '__main__':

    args = sys.argv
    if len(args) < 2:
        print("Usage: python3 docker_solr_init.py <collection name> <address>")
        sys.exit(-1)
    collection = args[1]

    client = SolrClient()
    if len(args) == 3:
        hostname = args[2]
        client = SolrClient(address=hostname)

    if not client.exists_collection(collection):
        print("Collection '%s' doesn't exists. Creating a new one..." % collection)
        created = client.create_collection(collection)
        if not created:
            sys.exit(-1)
    else:
        print("Collection '%s' exists. Updating indexes..." % collection)

    collection_data = client.status_collection(collection)
    indexed, _ = client.status_collection(collection)
    del _
    if indexed == 0:
        print("Performing a full reindex of '%s' collection..." % collection)
        p = subprocess.call(["python3", "manage.py", "rebuild_index", "--noinput"])