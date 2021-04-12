#!/usr/bin/env bash

SOLR_URL=${SOLR_URL-'http://localhost:8983/solr'}
SOLR_COLLECTION=${SOLR_COLLECTION-'sapl'}

curl -X POST "$SOLR_URL/admin/collections?action=DELETE&name=$SOLR_COLLECTION"