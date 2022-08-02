#!/usr/bin/env bash

while true; do
    COUNT_PG=`psql $1 -c '\l \q' | grep sapl | wc -l`
    if ! [ "$COUNT_PG" -eq "0" ]; then
       break
    fi
    echo "Waiting for Database Connection $1..."
    sleep 10
done

echo "Database is reachable!"
