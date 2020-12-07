#!/usr/bin/env bash

if [[ -z $SOLR_HOME ]]; then
  echo 'Cannot run script! You need to setup $SOLR_HOME'
  exit
fi

ZK_HOST=${ZK_HOST-'localhost:9983'}

$SOLR_HOME/bin/solr zk upconfig -n sapl_configset -d solr/sapl_configset/ -z $ZK_HOST
