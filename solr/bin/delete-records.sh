#!/usr/bin/env bash

SOLR_URL=${SOLR_URL-'http://localhost:8983/solr'}
SOLR_COLLECTION=${SOLR_COLLECTION-'sapl'}

curl -X POST "$SOLR_URL/$SOLR_COLLECTION/update?commit=true&stream.body=<delete><query>*%3A*</query></delete>"