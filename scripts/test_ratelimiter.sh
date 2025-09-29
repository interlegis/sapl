#!/bin/bash

#URL=http://localhost:8000/materia/4379
#URL=http://localhost:8000/norma/pesquisar
#URL=http://localhost/norma/pesquisar
#URL=https://sapl31demo.interlegis.leg.br/docadm/45
#URL=https://sapl.joaopessoa.pb.leg.br/materia/186300
#URL=http://localhost:8000/materia/4379/materiaassunto
#URL=http://localhost:8000/sessao/4984
URL="http://localhost:8000/docadm/pesq-doc-adm?tipo=&o=&numero=&complemento=&ano=&protocolo__numero=&numero_externo=&data_0=&data_1=&interessado=&assunto=&tramitacao=&tramitacaoadministrativo__status=&tramitacaoadministrativo__unidade_tramitacao_destino=&pesquisar=Pesquisar"

for i in $(seq 1 12); do
   curl -sS -o /dev/null -w "req=$i http=%{http_code} time=%{time_total}\n" "$URL"
done
