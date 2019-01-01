#!/bin/bash

# Pass the base SOLR URL as parameter, i.e., bash check_solr http://localhost:8983

SOLR_URL=$1

echo "Waiting for solr connection at $SOLR_URL ..."
while true; do
   echo "$SOLR_URL/solr/admin/collections?action=LIST"
   RESULT=$(curl -s -o /dev/null -I "$SOLR_URL/solr/admin/collections?action=LIST" -w '%{http_code}')
   echo $RESULT
   if [ "$RESULT" -eq '200' ]; then
      echo "Solr server is up!"
      break
   else
      sleep 3
   fi
done
