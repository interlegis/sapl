#!/bin/sh

while true; do
    COUNT_PG=`psql $1 -c '\l \q' | grep sapl | wc -l`
    if ! [ "$COUNT_PG" -eq "0" ]; then
       break
    fi
    echo "Esperando conexão com BD"
    sleep 10
done
