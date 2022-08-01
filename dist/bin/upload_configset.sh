#!/usr/bin/env bash

SOLR_USER=solr
SOLR_PASSWORD=SolrRocks
SOLR_HOST=localhost
SOLR_PORT=8983

CONFIGSET_NAME=sapl_configset
CONFIGSET_FILE=sapl_configset.zip

export SOLR_URL="http://$SOLR_USER:$SOLR_PASSWORD@$SOLR_HOST:$SOLR_PORT/solr/admin/configs?action=UPLOAD&name=$CONFIGSET_NAME&wt=json"
curl -X POST -L -F "file=@$CONFIGSET_FILE;type=application/zip" $SOLR_URL
