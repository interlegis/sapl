#!/bin/bash

#URL=http://localhost:8000/materia/4379
URL=http://localhost:8000/norma/pesquisar
#URL=http://localhost/norma/pesquisar

for i in $(seq 1 6); do
   curl -sS -o /dev/null -w "req=$i http=%{http_code} time=%{time_total}\n" "$URL"
done
