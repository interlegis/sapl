import requests

"""
    Imprime quantidade de colletions, qtd de documentos por collection e
    total de documentos indexados.
"""

BASE_URL='http://localhost:8983/solr'


if __name__=='__main__':

    resp = requests.get(BASE_URL+'/admin/collections?action=LIST')

    collections = sorted(resp.json()['collections'])

    largest_col = (None,-1)
    total_docs = 0
    
    print("Collection\t\t\tNumber of documents")
    print("--------------------------------------------------")
    
    for c in collections:
        r = requests.get(BASE_URL+'/{}/select?q=*:*&rows=0'.format(c))
        num_docs = r.json()['response']['numFound']
        total_docs += num_docs

        if num_docs >= largest_col[1]:
            largest_col = (c, num_docs)
        
        print("%30s\t%6s" % (c, num_docs))

    print("------------------------------------------")
    print("- Number of collections: %s\n" % len(collections))
    print("- Largest collection: '%s' (%s docs)\n" % largest_col)
    print("- Total documents accross all collections: %s\n" % total_docs)

