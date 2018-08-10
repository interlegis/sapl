
import requests
import logging
import subprocess
import sys


class SolrClient:

    # TODO: allow HTTPS and custom port
    STATUS_CORE = "{}://{}:{}/solr/admin/cores?action=STATUS&core={}&wt=json"
    EXISTS_CORE = "{}://{}:{}/solr/{}/admin/ping?wt=json"
    OPTIMIZE_CORE = "{}://{}:{}/solr/{}/update?optimize=true"
    CREATE_CORE = "{}://{}:{}/solr/admin/cores?action=CREATE&name={}&configSet=sapl_configset"
    DELETE_CORE = "{}://{}:{}/solr/admin/cores?" \
                  "action=UNLOAD&core={}&deleteIndex=true&deleteDataDir=true&deleteInstanceDir=true"
    DELETE_DATA = "{}://{}:{}/solr/{}/update?commitWithin=1000&overwrite=true&wt=json"

    def __init__(self, address='localhost', port=8983, protocol='http'):
        self.protocol = protocol
        self.address = address
        self.port = port

    def status_core(self, core_name):
        req_url = self.STATUS_CORE.format(self.protocol, self.address, self.port, core_name)
        return requests.post(req_url).json()

    def exists_core(self, core_name):
        req_url = self.EXISTS_CORE.format(self.protocol, self.address, self.port, core_name)
        res = requests.get(req_url)
        return True if res.ok else False

    def create_core(self, core_name):

        # UPLOAD configset
        subprocess.call(['cp', '-rv', './solr/sapl_configset', '/opt/solr/server/solr/configsets'])

        req_url = self.CREATE_CORE.format(self.protocol,
                                            self.address,
                                            self.port,
                                            core_name)

        res = requests.post(req_url)
        if res.ok:
            print("Core '%s' created succesfully" % core_name)
        else:
            print("Error creating core '%s'" % core_name)
            as_json = res.json()
            print("Error %s: %s" % (res.status_code, as_json['error']['msg']))
            return False
        return True

    def optimize_core(self, core_name):
        req_url = self.OPTIMIZE_CORE.format(self.protocol, self.address, self.port, core_name)
        res = requests.get(req_url)
        if not res.ok:
            print("Error optimizing core '{}'".format(core_name))
            print("Code {}: {}".format(res.status_code, res.text))
        else:
            print("Core '{}' optimized successfully!".format(core_name))
    
    def delete_core(self, core_name):
        req_url = self.DELETE_CORE.format(self.protocol, self.address, self.port, core_name)
        res = requests.post(req_url)
        if not res.ok:
            print("Error optimizing core '%s'", core_name)
            print("Code {}: {}".format(res.status_code, res.text))
        else:
            print("Core '%s' deleted successfully!" % core)

    def delete_data(self, core_name):
        req_url = self.DELETE_DATA.format(self.protocol, self.address, self.port, core_name)
        res = requests.post(req_url,
                            data='<delete><query>*:*</query></delete>',
                            headers={'Content-Type': 'application/xml'})
        if not res.ok:
            print("Error deleting index for core '%s'", core_name)
            print("Code {}: {}".format(res.status_code, res.text))
        else:
            print("Core '%s' data deleted successfully!" % core_name)

            data = self.status_core(core_name)
            prefix = data['status'][core_name]['index']
            print("Num docs: %s" % prefix['numDocs'])
            print("Delete docs: %s" % prefix['deletedDocs'])


if __name__ == '__main__':

    args = sys.argv
    if len(args) < 2:
        print("Usage: python3 docker_solr_init.py <core name> <address>")
        sys.exit(-1)
    core = args[1]

    client = SolrClient()
    if len(args) == 3:
        address = args[2]
        client = SolrClient(address=address)


    if not client.exists_core(core):
        print("Core '%s' doesn't exists. Creating a new one..." % core)
        created = client.create_core(core)

        if created:
            core_data = client.status_core(core)

            if len(core_data['status'][core]) == 0:
                print("Error getting core '%s', status: '%s'" % (core, core_data['initFailures'][core]))
            else:
                print("Performing a full reindex of '%s' core..." % core)
                p = subprocess.call(["python3", "manage.py", "rebuild_index --noinput"])
                client.optimize_core(core)

                num_docs = core_data['status'][core]['index']['numDocs']
                print("Docs indexes in core '{}': {}".format(core, num_docs))
    else:
        print("Core '%s' exists. Updating indexes..." % core)
        # subprocess.call(["python3", "manage.py", "update_index"])
        # client.optimize_core(core)