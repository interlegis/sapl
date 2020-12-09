#!/usr/bin/env bash

SOLR_URL=${SOLR_URL-'http://localhost:8983/solr'}
SOLR_COLLECTION=${SOLR_COLLECTION-'sapl'}

curl -X POST "$SOLR_URL/admin/collections?action=CREATE&name=$SOLR_COLLECTION&numShards=1&replicationFactor=1&collection.configName=sapl_configset"