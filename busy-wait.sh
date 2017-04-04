#!/bin/sh

#

while true; do
    COUNT_PG=`netstat -an | grep "tcp.*:5532.*LISTEN"| wc -l`
    if ! [ "$COUNT_PG" -eq "0" ]; then
       break
    fi
    echo "Esperando BD"
    sleep 5
done
