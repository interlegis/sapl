#!/bin/bash

# rodar esse script na raiz do projeto

parallel --verbose ./sapl/legacy/scripts/migra_um_db.sh :::: <(mysql -u root -padmin -e 'show databases;' | grep '^sapl_')
