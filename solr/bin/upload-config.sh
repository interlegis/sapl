#!/usr/bin/env bash

SOLR_URL=${SOLR_URL-'http://localhost:8983/solr'}

# zip configset sapl_configset
cd ../sapl_configset/conf && zip -r sapl_configset.zip .

curl -X POST --header "Content-Type:application/octet-stream" --data-binary @sapl_configset.zip "$SOLR_URL/admin/configs?action=UPLOAD&name=sapl_configset"

cd -
rm ../sapl_configset/conf/sapl_configset.zip