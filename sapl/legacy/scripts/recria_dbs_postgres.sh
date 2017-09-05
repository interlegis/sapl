# (Re)cria todos os bancos postgres para migração
# cria um banco postgres (de mesmo nome) para cada banco mysql cujo nome começa com "sapl_"

mysql -u root -padmin -e 'show databases;' | grep '^sapl_' | grep -v '_copy$' | xargs -I{} ./recria_um_db_postgres.sh {}

